#!/usr/bin/env python3
"""
Master Daoist Medical Canon Scraper
Targets: HDNJ (13), JGYL (14), NanJing (15), BCGM (16)

Key design:
- API first (ctext.org /gettext). When rate-limited, wait 30 min ONCE then move on.
- HTML fallback with /zh suffix. 2 tries max (5 min apart), then log & SKIP.
- Never get stuck on a single chapter for hours.
- Rotating User-Agents, 8-15s polite sleep between every request.
- State tracking: resume from where left off.
"""

import re
import sys
import time
import random
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(RAW_DIR / "scrape_log.txt", mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("canon")

REQUEST_TIMEOUT = 45
SLEEP_MIN, SLEEP_MAX = 8, 15       # between every request
HTML_RETRY_WAIT = 5 * 60           # 5 min wait before one HTML retry
API_RATELIMIT_WAIT = 30 * 60       # 30 min wait when API rate-limited

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
CAPTCHA_MARKERS = ["認證圖案", "Validation image", "captcha-form"]
SKIP_PHRASES = [
    "Chinese Text Project", "Log in", "Jump to dictionary",
    "Show parallel", "Please help", "copyright",
]

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Session-level flag: disable API after persistent rate limiting
_api_disabled = False


def _headers() -> dict:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "DNT": "1",
        "Cache-Control": "max-age=0",
    }


def polite_sleep(label: str = "") -> None:
    secs = random.uniform(SLEEP_MIN, SLEEP_MAX)
    log.info(f"  zzz {secs:.1f}s{' [' + label + ']' if label else ''}")
    time.sleep(secs)


def is_captcha(text: str) -> bool:
    return any(m in text for m in CAPTCHA_MARKERS)


def fetch_api(urn: str, session: requests.Session) -> list[str] | None:
    """
    Try ctext.org API. Returns CJK paragraphs or None.
    On ERR_REQUEST_LIMIT: wait 30 min, retry once. Still limited → disable API.
    """
    global _api_disabled
    if _api_disabled:
        return None

    for attempt in range(2):
        try:
            resp = session.get(
                f"https://api.ctext.org/gettext?urn={urn}",
                headers=_headers(), timeout=REQUEST_TIMEOUT
            )
            resp.raise_for_status()
            data = resp.json()
            if "fulltext" in data:
                return [t for t in data["fulltext"] if CJK_RE.search(t)]
            if "error" in data:
                code = data["error"].get("code", "")
                if "REQUEST_LIMIT" in code or "LIMIT" in code:
                    if attempt == 0:
                        log.warning(f"  API rate-limited. Waiting 30 min then retrying...")
                        time.sleep(API_RATELIMIT_WAIT)
                        continue
                    else:
                        log.warning("  API still rate-limited after wait. Disabling API for session.")
                        _api_disabled = True
                        return None
                elif "AUTH" in code:
                    log.debug(f"  API auth required: {urn}")
                    return None
                else:
                    log.debug(f"  API error {code}: {urn}")
                    return None
        except Exception as exc:
            log.debug(f"  API exception ({urn}): {exc}")
            return None
    return None


def fetch_html_once(url: str, session: requests.Session) -> requests.Response | None:
    """Single HTML fetch attempt. Returns response or None (404/403/CAPTCHA)."""
    try:
        resp = session.get(url, headers=_headers(), timeout=REQUEST_TIMEOUT)
        if resp.status_code == 404:
            return None
        if resp.status_code in (403, 429):
            log.warning(f"  HTML {resp.status_code}: {url}")
            return "BLOCKED"  # signal to caller
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        if is_captcha(resp.text):
            log.warning(f"  HTML CAPTCHA: {url}")
            return "BLOCKED"
        return resp
    except requests.RequestException as exc:
        log.error(f"  HTML error ({url}): {exc}")
        return None


def fetch_html(url: str, session: requests.Session) -> requests.Response | None:
    """
    Fetch HTML with one retry on block. 2 attempts max (5 min apart).
    Returns response, or None (404), or "BLOCKED" (persistent 403).
    """
    result = fetch_html_once(url, session)
    if result == "BLOCKED":
        log.info(f"  Waiting {HTML_RETRY_WAIT//60} min before HTML retry...")
        time.sleep(HTML_RETRY_WAIT)
        result = fetch_html_once(url, session)
        if result == "BLOCKED":
            log.warning(f"  HTML still blocked after retry. Skipping.")
            return "BLOCKED"
    return result


def extract_chinese(soup: BeautifulSoup) -> str:
    paragraphs = []
    for td in soup.find_all("td", class_="ctext"):
        t = td.get_text(separator="\n", strip=True)
        if t and CJK_RE.search(t):
            paragraphs.append(t)
    if not paragraphs:
        content = soup.find(id="content")
        if content:
            for elem in content.find_all(["p", "td", "div"], recursive=True):
                t = elem.get_text(separator=" ", strip=True)
                if t and len(t) > 5 and CJK_RE.search(t):
                    if not any(s in t for s in SKIP_PHRASES):
                        paragraphs.append(t)
    if not paragraphs:
        for td in soup.find_all("td"):
            t = td.get_text(separator=" ", strip=True)
            if t and len(t) > 10 and CJK_RE.search(t):
                if not any(s in t for s in SKIP_PHRASES):
                    paragraphs.append(t)
    seen, unique = set(), []
    for p in paragraphs:
        p = p.strip()
        if p and p not in seen:
            seen.add(p)
            unique.append(p)
    return "\n\n".join(unique)


def parse_file_chapters(filepath: Path) -> dict[str, str]:
    chapters: dict[str, str] = {}
    if not filepath.exists():
        return chapters
    current, lines = None, []
    for line in filepath.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^=== (.+?) ===$", line.strip())
        if m:
            if current is not None:
                chapters[current] = "\n".join(lines).strip()
            current, lines = m.group(1), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        chapters[current] = "\n".join(lines).strip()
    return chapters


def chapter_is_clean(content: str) -> bool:
    if not content or is_captcha(content):
        return False
    return len(CJK_RE.findall(content)) >= 50


def append_chapter(filepath: Path, title: str, content: str) -> None:
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n\n=== {title} ===\n\n{content.strip()}\n")


def fetch_chapter(base_path: str, urn: str, session: requests.Session) -> tuple[str | None, str]:
    """
    Try API then HTML (/zh, then bare). Returns (text_or_None, method_used).
    """
    # 1. API
    api_data = fetch_api(urn, session)
    if api_data and len("".join(api_data)) >= 30:
        return "\n\n".join(api_data), "API"

    # 2. HTML /zh
    for suffix in ("/zh", ""):
        url = f"https://ctext.org/{base_path}{suffix}"
        resp = fetch_html(url, session)
        if resp is None:
            return None, "404"
        if resp == "BLOCKED":
            continue  # try bare URL
        text = extract_chinese(BeautifulSoup(resp.text, "html.parser"))
        if text and len(CJK_RE.findall(text)) >= 30:
            return text, f"HTML{suffix}"

    return None, "FAILED"


# ══════════════════════════════════════════════════════════════════════════════
# Chapter catalogues
# ══════════════════════════════════════════════════════════════════════════════

HDNJ_SUWEN = [
    ("shang-gu-tian-zhen-lun", "上古天真論"),
    ("si-qi-diao-shen-da-lun", "四氣調神大論"),
    ("sheng-qi-tong-tian-lun", "生氣通天論"),
    ("jin-gui-zhen-yan-lun", "金匱真言論"),
    ("yin-yang-ying-xiang-da-lun", "陰陽應象大論"),
    ("yin-yang-li-he-lun", "陰陽離合論"),
    ("yin-yang-bie-lun", "陰陽別論"),
    ("ling-lan-mi-dian-lun", "靈蘭秘典論"),
    ("liu-jie-cang-xiang-lun", "六節藏象論"),
    ("wu-cang-sheng-cheng", "五藏生成"),
    ("wu-cang-bie-lun", "五藏別論"),
    ("yi-fa-fang-yi-lun", "異法方宜論"),
    ("yi-jing-bian-qi-lun", "移精變氣論"),
    ("tang-ye-lao-li-lun", "湯液醪醴論"),
    ("yu-ban-lun-yao", "玉版論要"),
    ("zhen-yao-jing-zhong-lun", "診要經終論"),
    ("mai-yao-jing-wei-lun", "脈要精微論"),
    ("ping-ren-qi-xiang-lun", "平人氣象論"),
    ("yu-ji-zhen-cang-lun", "玉機真藏論"),
    ("san-bu-jiu-hou-lun", "三部九候論"),
    ("jing-mai-bie-lun", "經脈別論"),
    ("cang-qi-fa-shi-lun", "藏氣法時論"),
    ("xuan-ming-wu-qi", "宣明五氣"),
    ("xie-qi-xing-zhi", "血氣形志"),
    ("bao-ming-quan-xing-lun", "寶命全形論"),
    ("ba-zheng-shen-ming-lun", "八正神明論"),
    ("li-he-zhen-xie", "離合真邪"),
    ("tong-ping-xu-shi-lun", "通評虛實論"),
    ("tai-yin-yang-ming-lun", "太陰陽明論"),
    ("yang-ming-mai-jie", "陽明脈解"),
    ("re-lun", "熱論"),
    ("ci-re", "刺熱"),
    ("ping-re-bing-lun", "評熱病論"),
    ("ni-diao-lun", "逆調論"),
    ("nve-lun", "瘧論"),
    ("ci-nve", "刺瘧"),
    ("qi-jue-lun", "氣厥論"),
    ("kai-lun", "欬論"),
    ("ju-tong-lun", "舉痛論"),
    ("fu-zhong-lun", "腹中論"),
    ("ci-yao-tong", "刺腰痛"),
    ("feng-lun", "風論"),
    ("bi-lun", "痺論"),
    ("wei-lun", "痿論"),
    ("jue-lun", "厥論"),
    ("bing-neng-lun", "病能論"),
    ("qi-bing-lun", "奇病論"),
    ("da-qi-lun", "大奇論"),
    ("mai-jie", "脈解"),
    ("ci-yao-lun", "刺要論"),
    ("ci-qi-lun", "刺齊論"),
    ("ci-jin-lun", "刺禁論"),
    ("ci-zhi-lun", "刺志論"),
    ("zhen-jie", "鍼解"),
    ("chang-ci-jie-lun", "長刺節論"),
    ("pi-bu-lun", "皮部論"),
    ("jing-luo-lun", "經絡論"),
    ("qi-xue-lun", "氣穴論"),
    ("qi-fu-lun", "氣府論"),
    ("gu-kong-lun", "骨空論"),
    ("shui-re-xue-lun", "水熱穴論"),
    ("diao-jing-lun", "調經論"),
    ("mou-ci-lun", "繆刺論"),
    ("si-shi-ci-ni-cong-lun", "四時刺逆從論"),
    ("biao-ben-bing-zhuan-lun", "標本病傳論"),
    ("tian-yuan-ji-da-lun", "天元紀大論"),
    ("wu-yun-xing-da-lun", "五運行大論"),
    ("liu-wei-zhi-da-lun", "六微旨大論"),
    ("qi-jiao-bian-da-lun", "氣交變大論"),
    ("wu-chang-zheng-da-lun", "五常政大論"),
    ("liu-yuan-zheng-ji-da-lun", "六元正紀大論"),
    ("ci-fa-lun", "刺法論"),
    ("ben-bing-lun", "本病論"),
    ("zhi-zhen-yao-da-lun", "至真要大論"),
    ("zhu-zhi-jiao-lun", "著至教論"),
    ("shi-cong-rong-lun", "示從容論"),
    ("shu-wu-guo-lun", "疏五過論"),
    ("zheng-si-shi-lun", "徵四失論"),
    ("yin-yang-lei-lun", "陰陽類論"),
    ("fang-sheng-shuai-lun", "方盛衰論"),
    ("jie-jing-wei-lun", "解精微論"),
]

HDNJ_LINGSHU = [
    ("jiu-zhen-shi-er-yuan", "九鍼十二原"),
    ("ben-shu", "本輸"),
    ("xiao-zhen-jie", "小鍼解"),
    ("xie-qi-cang-fu-bing-xing", "邪氣藏府病形"),
    ("gen-jie", "根結"),
    ("shou-yao-gang-rou", "壽夭剛柔"),
    ("guan-zhen", "官鍼"),
    ("ben-shen", "本神"),
    ("zhong-shi", "終始"),
    ("jing-mai", "經脈"),
    ("jing-bie", "經別"),
    ("jing-shui", "經水"),
    ("jing-jin", "經筋"),
    ("gu-du", "骨度"),
    ("wu-shi-ying", "五十營"),
    ("ying-qi", "營氣"),
    ("mai-du", "脈度"),
    ("ying-wei-sheng-hui", "營衛生會"),
    ("si-shi-qi", "四時氣"),
    ("wu-xie", "五邪"),
    ("han-re-bing", "寒熱病"),
    ("lai-kuang-bing", "癩狂病"),
    ("re-bing", "熱病"),
    ("jue-bing", "厥病"),
    ("bing-ben", "病本"),
    ("za-bing", "雜病"),
    ("zhou-bi", "周痺"),
    ("kou-wen", "口問"),
    ("shi-zhuan", "師傳"),
    ("jue-qi", "決氣"),
    ("chang-wei", "腸胃"),
    ("ping-ren-jue-gu", "平人絕穀"),
    ("hai-lun", "海論"),
    ("wu-luan", "五亂"),
    ("zhang-lun", "脹論"),
    ("wu-long-jin-ye-bie", "五癃津液別"),
    ("wu-yue-wu-shi", "五閱五使"),
    ("ni-shun-fei-shou", "逆順肥瘦"),
    ("xie-luo-lun", "血絡論"),
    ("yin-yang-qing-zhuo", "陰陽清濁"),
    ("yin-yang-xi-ri-yue", "陰陽繫日月"),
    ("bing-zhuan", "病傳"),
    ("yin-xie-fa-meng", "淫邪發夢"),
    ("shun-qi-yi-ri-fen-wei", "順氣一日分為四時"),
    ("wai-chuai", "外揣"),
    ("wu-bian", "五變"),
    ("ben-cang", "本藏"),
    ("jin-fu", "禁服"),
    ("wu-se", "五色"),
    ("lun-yong", "論勇"),
    ("bei-yu", "背腧"),
    ("wei-qi", "衛氣"),
    ("lun-tong", "論痛"),
    ("tian-nian", "天年"),
    ("ni-shun", "逆順"),
    ("wu-wei", "五味"),
    ("shui-zhang", "水脹"),
    ("zei-feng", "賊風"),
    ("wei-qi-shi-chang", "衛氣失常"),
    ("yu-ban", "玉版"),
    ("wu-jin", "五禁"),
    ("dong-shu", "動輸"),
    ("wu-wei-lun", "五味論"),
    ("yin-yang-er-shi-wu-ren", "陰陽二十五人"),
    ("wu-yin-wu-wei", "五音五味"),
    ("bai-bing-shi-sheng", "百病始生"),
    ("xing-zhen", "行鍼"),
    ("shang-ge", "上膈"),
    ("you-hui-wu-yan", "憂恚無言"),
    ("han-re", "寒熱"),
    ("xie-ke", "邪客"),
    ("tong-tian", "通天"),
    ("guan-neng", "官能"),
    ("lun-ji-zhen-chi", "論疾診尺"),
    ("ci-jie-zhen-xie", "刺節真邪"),
    ("wei-qi-xing", "衛氣行"),
    ("jiu-gong-ba-feng", "九宮八風"),
    ("jiu-zhen-lun", "九鍼論"),
    ("sui-lu-lun", "歲露論"),
    ("da-huo-lun", "大惑論"),
    ("yong-ju", "癰疽"),
]

JGYL_CHAPTERS = [
    ("zang-fu-jing-luo-xian-hou-bing-mai-zheng", "藏府經絡先後病脈證"),
    ("jing-shi-ye-bing-mai-zheng", "痙濕暍病脈證"),
    ("bai-he-hu-huo-yin-yang-du-bing-zheng-zhi", "百合狐惑陰陽毒病證治"),
    ("nve-bing-mai-zheng-bing-zhi", "瘧病脈證並治"),
    ("zhong-feng-li-jie-bing-mai-zheng-bing-zhi", "中風歷節病脈證並治"),
    ("xue-bi-xu-lao-bing-mai-zheng-bing-zhi", "血痺虛勞病脈證並治"),
    ("fei-wei-fei-yong-ke-sou-shang-qi-bing-mai-zheng-zhi", "肺痿肺癰欬嗽上氣病脈證治"),
    ("ben-tun-qi-bing-mai-zheng-zhi", "奔豚氣病脈證治"),
    ("xiong-bi-xin-tong-duan-qi-bing-mai-zheng-zhi", "胸痺心痛短氣病脈證治"),
    ("fu-man-han-shan-su-shi-bing-mai-zheng-zhi", "腹滿寒疝宿食病脈證治"),
    ("wu-cang-feng-han-ji-ju-bing-mai-zheng-bing-zhi", "五藏風寒積聚病脈證並治"),
    ("tan-yin-ke-sou-bing-mai-zheng-bing-zhi", "痰飲欬嗽病脈證並治"),
    ("xiao-ke-xiao-bian-li-lin-bing-mai-zheng-bing-zhi", "消渴小便利淋病脈證並治"),
    ("shui-qi-bing-mai-zheng-bing-zhi", "水氣病脈證並治"),
    ("huang-dan-bing-mai-zheng-bing-zhi", "黃疸病脈證並治"),
    ("jing-ji-tu-nv-xia-xue-xiong-man-yu-xue-bing-mai-zheng-zhi", "驚悸吐衄下血胸滿瘀血病脈證治"),
    ("ou-tu-huo-xia-li-bing-mai-zheng-zhi", "嘔吐噦下利病脈證治"),
    ("chuang-yong-chang-yong-jin-yin-bing-mai-zheng-bing-zhi", "瘡癰腸癰浸淫病脈證並治"),
    ("fu-jue-shou-zhi-bi-zhong-zhuan-jin-yin-hu-shan-hui-chong-bing-mai-zheng-zhi", "趺蹶手指臂腫轉筋陰狐疝蚘蟲病脈證治"),
    ("fu-ren-ren-shen-bing-mai-zheng-bing-zhi", "婦人妊娠病脈證並治"),
    ("fu-ren-chan-hou-bing-mai-zheng-zhi", "婦人產後病脈證治"),
    ("fu-ren-za-bing-mai-zheng-bing-zhi", "婦人雜病脈證並治"),
    ("za-liao-fang", "雜療方"),
    ("qin-shou-yu-chong-jin-ji-bing-zhi", "禽獸魚蟲禁忌並治"),
    ("guo-shi-cai-gu-jin-ji-bing-zhi", "果實菜穀禁忌並治"),
]

NANJING_FALLBACK = [
    ("jing-mai-zhen-hou", "經脈診候"),
    ("jing-luo-da-shu", "經絡大數"),
    ("qi-jing-ba-mai", "奇經八脈"),
    ("rong-wei-san-jiao", "榮衛三焦"),
    ("cang-fu-pei-xiang", "藏府配像"),
    ("cang-fu-du-shu", "藏府度數"),
    ("xu-shi-xie-zheng", "虛實邪正"),
    ("cang-fu-zhuan-bing", "藏府傳病"),
    ("shen-sheng-gong-qiao", "神聖工巧"),
    ("cang-fu-jing-yu", "藏府井俞"),
    ("yong-zhen-bu-xie", "用鍼補瀉"),
]


# ══════════════════════════════════════════════════════════════════════════════
# Book scrapers
# ══════════════════════════════════════════════════════════════════════════════

def scrape_book(
    out: Path,
    chapters: list[tuple[str, str]],   # [(slug, title)]
    base_prefix: str,                   # e.g. "huangdi-neijing"
    urn_prefix: str,                    # e.g. "ctp:huangdi-neijing"
    book_tag: str,
    session: requests.Session,
    header: str = "",
) -> None:
    existing = parse_file_chapters(out)
    need = [(slug, title) for slug, title in chapters
            if not chapter_is_clean(existing.get(title, ""))]
    log.info(f"[{book_tag}] {len(chapters)-len(need)} already clean, {len(need)} to fetch")

    if not out.exists() and header:
        out.write_text(f"{header}\n\n", encoding="utf-8")

    skipped = []
    for i, (slug, title) in enumerate(need, 1):
        log.info(f"[{book_tag}] {i}/{len(need)}: {title}")
        text, method = fetch_chapter(f"{base_prefix}/{slug}", f"{urn_prefix}/{slug}", session)

        if text:
            append_chapter(out, title, text)
            log.info(f"  ✓ {method}: {len(text)} chars")
        elif method == "404":
            append_chapter(out, title, "[CHAPTER MISSING - 404]")
            log.warning(f"  ✗ 404: {title}")
        else:
            append_chapter(out, title, "[CHAPTER SKIPPED - server blocked, re-run later]")
            log.warning(f"  ✗ SKIPPED ({method}): {title}")
            skipped.append(title)

        if i < len(need):
            polite_sleep(book_tag)

    if skipped:
        log.warning(f"[{book_tag}] {len(skipped)} chapters skipped (blocked): {skipped[:5]}{'...' if len(skipped)>5 else ''}")
    log.info(f"[{book_tag}] Done → {out}  ({out.stat().st_size//1024}KB)")


def scrape_hdnj(session: requests.Session) -> None:
    out = RAW_DIR / "13_tcm_hdnj_chinese.txt"
    chapters = (
        [(s, t) for s, t in HDNJ_SUWEN]
        + [(s, t) for s, t in HDNJ_LINGSHU]
    )
    scrape_book(out, chapters, "huangdi-neijing", "ctp:huangdi-neijing",
                "HDNJ", session, header="=== 黃帝內經 ===")


def scrape_jgyl(session: requests.Session) -> None:
    out = RAW_DIR / "14_tcm_jgyl_chinese.txt"
    scrape_book(out, JGYL_CHAPTERS, "jin-gui-yao-lue", "ctp:jin-gui-yao-lue",
                "JGYL", session, header="=== 金匱要略 ===")


def scrape_nanjing(session: requests.Session) -> None:
    out = RAW_DIR / "15_tcm_nanjing_chinese.txt"

    polite_sleep("NanJing TOC")
    resp = fetch_html("https://ctext.org/nan-jing", session)
    chapters = list(NANJING_FALLBACK)
    if resp and resp != "BLOCKED":
        soup = BeautifulSoup(resp.text, "html.parser")
        found, seen = [], set()
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if not href.startswith("nan-jing/"):
                continue
            slug = href.split("/", 1)[1]
            if "/" in slug or "." in slug or slug in ("zh", "ens") or slug in seen:
                continue
            seen.add(slug)
            title = a.get_text(strip=True)
            cjk = "".join(c for c in title if "\u4e00" <= c <= "\u9fff")
            found.append((slug, cjk or title))
        if found:
            chapters = found
            log.info(f"[NanJing] TOC: {len(chapters)} chapters")
    polite_sleep("post-TOC")

    scrape_book(out, chapters, "nan-jing", "ctp:nan-jing",
                "NanJing", session, header="=== 難經 ===")


def scrape_bcgm(session: requests.Session) -> None:
    out = RAW_DIR / "16_tcm_bcgm_chinese.txt"

    polite_sleep("BCGM TOC")
    toc_url = "https://ctext.org/wiki.pl?if=en&res=8"
    resp = fetch_html(toc_url, session)
    if not resp or resp == "BLOCKED":
        log.error("[BCGM] TOC fetch failed")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    chapters: list[tuple[str, str]] = []
    seen_ids: set[str] = set()
    ch_urls: dict[str, str] = {}

    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "chapter=" not in href:
            continue
        full_url = urljoin(toc_url, href)
        qs = parse_qs(urlparse(full_url).query)
        ch_id = qs.get("chapter", [None])[0]
        if ch_id and ch_id not in seen_ids:
            seen_ids.add(ch_id)
            title = a.get_text(strip=True) or f"ch_{ch_id}"
            chapters.append((ch_id, title))
            ch_urls[ch_id] = full_url

    log.info(f"[BCGM] TOC: {len(chapters)} chapters")
    polite_sleep("post-BCGM-TOC")

    existing = parse_file_chapters(out)
    need = [(ch_id, title) for ch_id, title in chapters
            if not chapter_is_clean(existing.get(title, ""))]
    log.info(f"[BCGM] {len(chapters)-len(need)} clean, {len(need)} to fetch")

    if not out.exists():
        out.write_text("=== 本草綱目 ===\n\n", encoding="utf-8")

    for i, (ch_id, title) in enumerate(need, 1):
        log.info(f"[BCGM] {i}/{len(need)}: {title} (id={ch_id})")

        api_data = fetch_api(f"ctp:ws{ch_id}", session)
        text = None
        if api_data and len("".join(api_data)) >= 20:
            text = "\n\n".join(api_data)
            log.info(f"  ✓ API {len(text)} chars")

        if not text:
            gb_url = ch_urls[ch_id].replace("if=en", "if=gb")
            resp2 = fetch_html(gb_url, session)
            if resp2 is None:
                append_chapter(out, title, "[CHAPTER MISSING - 404]")
                log.warning(f"  ✗ 404: {title}")
                if i < len(need): polite_sleep("BCGM")
                continue
            if resp2 == "BLOCKED":
                append_chapter(out, title, "[CHAPTER SKIPPED - server blocked, re-run later]")
                log.warning(f"  ✗ SKIPPED: {title}")
                if i < len(need): polite_sleep("BCGM")
                continue
            text = extract_chinese(BeautifulSoup(resp2.text, "html.parser"))
            if text and len(CJK_RE.findall(text)) >= 10:
                log.info(f"  ✓ HTML {len(text)} chars")
            else:
                text = None

        if text:
            append_chapter(out, title, text)
        else:
            append_chapter(out, title, "[CHAPTER EMPTY - no CJK text extracted]")
            log.warning(f"  ✗ empty: {title}")

        if i < len(need):
            polite_sleep("BCGM")

    log.info(f"[BCGM] Done → {out}  ({out.stat().st_size//1024}KB)")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    log.info("=" * 60)
    log.info("Daoist Medical Canon Scrape — START (v2, no-stuck)")
    log.info("=" * 60)

    session = requests.Session()

    for label, fn in [
        ("BOOK 1/4: 黃帝內經", scrape_hdnj),
        ("BOOK 2/4: 金匱要略", scrape_jgyl),
        ("BOOK 3/4: 難經", scrape_nanjing),
        ("BOOK 4/4: 本草綱目", scrape_bcgm),
    ]:
        log.info(f"\n>>> {label}")
        try:
            fn(session)
        except Exception as exc:
            log.error(f"{label} crashed: {exc}", exc_info=True)
        log.info("  === 30s inter-book cooldown ===")
        time.sleep(30)

    log.info("\n" + "=" * 60)
    log.info("ALL BOOKS COMPLETE")
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
