#!/usr/bin/env python3
"""
Wikisource Scraper — Daoist Medical Canon
Sources: zh.wikisource.org (free, no auth, no rate-limit traps)

Targets:
  13_tcm_hdnj_chinese.txt  — 黃帝內經 (Suwen 卷1-24 + Lingshu 卷1-12)
  14_tcm_jgyl_chinese.txt  — 金匱要略 (single page)
  15_tcm_nanjing_chinese.txt — 難經 (single page, 81 difficulties)
  16_tcm_bcgm_chinese.txt  — 本草綱目 (66 category sections)

Strategy:
  - MediaWiki API (action=query, rvprop=content) → raw wikitext
  - Custom wikitext stripper → clean Chinese
  - 2-4s polite sleep between every API call
  - State tracking: check existing file sections before fetching
  - Missing-chapters report written to data/raw/missing_report.txt
"""

import re
import sys
import time
import random
import logging
from pathlib import Path

import requests

# ── Setup ──────────────────────────────────────────────────────────────────────
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(RAW_DIR / "wikisource_scrape.log", mode="a", encoding="utf-8"),
    ],
)
log = logging.getLogger("ws")

API_URL   = "https://zh.wikisource.org/w/api.php"
HEADERS   = {"User-Agent": "almanac-research-bot/1.0 (educational; classical-chinese-texts)"}
SLEEP_MIN = 2.0
SLEEP_MAX = 4.5
CJK_RE    = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")


# ── API helpers ────────────────────────────────────────────────────────────────

def polite_sleep() -> None:
    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))


def fetch_wikitext(title: str) -> str | None:
    """Fetch raw wikitext for a Wikisource page title. Returns None if missing."""
    try:
        resp = requests.get(API_URL, params={
            "action": "query", "titles": title,
            "prop": "revisions", "rvprop": "content",
            "rvslots": "main", "format": "json",
        }, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        pages = resp.json()["query"]["pages"]
        for pid, page in pages.items():
            if pid == "-1":
                return None
            revs = page.get("revisions", [])
            if not revs:
                return None
            return revs[0].get("slots", {}).get("main", {}).get("*", None)
    except Exception as exc:
        log.error(f"  API error fetching '{title}': {exc}")
        return None


def fetch_subpages(prefix: str, limit: int = 200) -> list[str]:
    """Return all page titles in namespace 0 starting with prefix."""
    try:
        resp = requests.get(API_URL, params={
            "action": "query", "list": "allpages",
            "apprefix": prefix, "aplimit": str(limit),
            "apnamespace": "0", "format": "json",
        }, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return [p["title"] for p in resp.json()["query"].get("allpages", [])]
    except Exception as exc:
        log.error(f"  API error listing '{prefix}': {exc}")
        return []


# ── Wikitext → Clean Chinese ───────────────────────────────────────────────────

def wikitext_to_chinese(wikitext: str) -> str:
    """
    Strip wikitext markup and return clean Chinese text.
    Preserves section headers as 【title】 markers.
    """
    t = wikitext

    # Remove <ref>...</ref> footnotes (keep their content out)
    t = re.sub(r"<ref[^>]*>.*?</ref>", "", t, flags=re.DOTALL)
    t = re.sub(r"<ref[^/]*/?>", "", t)

    # Remove {{...}} templates (iterate for nesting)
    for _ in range(6):
        t = re.sub(r"\{\{[^{}]*\}\}", "", t)

    # Remove {|....|} wikitables
    t = re.sub(r"\{\|.*?\|\}", "", t, flags=re.DOTALL)

    # Remove [[File:|Image: embeds]]
    t = re.sub(r"\[\[(File|Image|圖像|文件|档案):[^\]]*\]\]", "", t, flags=re.IGNORECASE)

    # [[link|display]] → display text
    t = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", t)
    # [[link]] → link text
    t = re.sub(r"\[\[([^\]]*)\]\]", r"\1", t)

    # External links [URL text] → text; bare [URL] → remove
    t = re.sub(r"\[https?://\S+\s+([^\]]+)\]", r"\1", t)
    t = re.sub(r"\[https?://\S+\]", "", t)

    # Convert wiki headers ==Title== → \n\n【Title】\n
    t = re.sub(r"={2,}\s*(.+?)\s*={2,}", r"\n\n【\1】\n", t)

    # Remove remaining HTML tags
    t = re.sub(r"<[^>]+>", "", t)

    # Remove wiki list/indent markers at line start
    t = re.sub(r"^[*#:;]+\s*", "", t, flags=re.MULTILINE)

    # Remove lines that are purely editorial footnote markers like [1] 注：...
    t = re.sub(r"^\[\d+\][^\n]*", "", t, flags=re.MULTILINE)

    # Remove lines with no CJK at all
    lines_out = []
    for line in t.splitlines():
        line = line.strip()
        if not line:
            continue
        if not CJK_RE.search(line):
            continue
        # Skip obvious boilerplate / metadata
        if any(s in line for s in ["Category:", "DEFAULTSORT:", "wikisource", "Wikipedia"]):
            continue
        lines_out.append(line)

    # Re-join, collapsing multiple blank lines
    return "\n\n".join(lines_out)


# ── File state helpers ─────────────────────────────────────────────────────────

def parse_sections(filepath: Path) -> dict[str, str]:
    """Return {section_title: content} from a file with === title === markers."""
    sections: dict[str, str] = {}
    if not filepath.exists():
        return sections
    current, lines = None, []
    for line in filepath.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^=== (.+?) ===$", line.strip())
        if m:
            if current is not None:
                sections[current] = "\n".join(lines).strip()
            current, lines = m.group(1), []
        elif current is not None:
            lines.append(line)
    if current is not None:
        sections[current] = "\n".join(lines).strip()
    return sections


def section_is_clean(content: str) -> bool:
    return len(CJK_RE.findall(content)) >= 80


def append_section(filepath: Path, title: str, content: str) -> None:
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"\n\n=== {title} ===\n\n{content.strip()}\n")


# ── Missing report ─────────────────────────────────────────────────────────────

_missing: list[str] = []

def log_missing(book: str, section: str, reason: str) -> None:
    entry = f"[{book}] {section}: {reason}"
    _missing.append(entry)
    log.warning(f"  MISSING: {entry}")


def write_missing_report() -> None:
    report_path = RAW_DIR / "missing_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("Missing Chapters Report — Wikisource Scrape\n")
        f.write("=" * 50 + "\n\n")
        if _missing:
            f.write(f"Total missing: {len(_missing)}\n\n")
            for entry in _missing:
                f.write(f"  • {entry}\n")
            f.write("\nThese sections were not found on zh.wikisource.org.\n")
            f.write("Recommend fetching from ctext.org once rate limits reset.\n")
        else:
            f.write("All sections found and downloaded successfully.\n")
    log.info(f"Missing report → {report_path}  ({len(_missing)} items)")


# ══════════════════════════════════════════════════════════════════════════════
# Book 1: 黃帝內經 — Suwen (卷1-24, skip 21) + Lingshu (卷1-12)
# ══════════════════════════════════════════════════════════════════════════════

SUWEN_VOLS  = [f"卷{str(i).zfill(2)}" for i in range(1, 25) if i != 21]  # 23 vols
LINGSHU_VOLS = [f"卷{str(i).zfill(2)}" for i in range(1, 13)]             # 12 vols

SUWEN_BASE   = "黄帝内經素問 (四庫全書本)"
LINGSHU_BASE = "靈樞經 (四庫全書本)"


def scrape_hdnj() -> None:
    out = RAW_DIR / "13_tcm_hdnj_chinese.txt"
    existing = parse_sections(out)

    chapters = (
        [(f"素問·{v}", f"{SUWEN_BASE}/{v}") for v in SUWEN_VOLS]
        + [(f"靈樞·{v}", f"{LINGSHU_BASE}/{v}") for v in LINGSHU_VOLS]
    )
    need = [(title, ws_title) for title, ws_title in chapters
            if not section_is_clean(existing.get(title, ""))]

    log.info(f"[HDNJ] {len(chapters)-len(need)} sections already clean, {len(need)} to fetch")

    if not out.exists():
        out.write_text("=== 黃帝內經 ===\n\n來源：zh.wikisource.org\n", encoding="utf-8")

    for i, (title, ws_title) in enumerate(need, 1):
        log.info(f"[HDNJ] {i}/{len(need)}: {title}")
        wt = fetch_wikitext(ws_title)
        polite_sleep()

        if wt is None:
            log_missing("HDNJ", title, f"Page not found on Wikisource: {ws_title}")
            append_section(out, title, "[CHAPTER MISSING — not on Wikisource; fetch from ctext.org]")
            continue

        text = wikitext_to_chinese(wt)
        cjk_count = len(CJK_RE.findall(text))

        if cjk_count >= 80:
            append_section(out, title, text)
            log.info(f"  ✓ {cjk_count} CJK chars")
        else:
            log_missing("HDNJ", title, f"Extracted only {cjk_count} CJK chars (too sparse)")
            append_section(out, title, f"[SPARSE — only {cjk_count} CJK chars; fetch from ctext.org]\n\n{text}")

    size_kb = out.stat().st_size // 1024
    log.info(f"[HDNJ] Done → {out} ({size_kb}KB)")


# ══════════════════════════════════════════════════════════════════════════════
# Book 2: 金匱要略 — single page
# ══════════════════════════════════════════════════════════════════════════════

def scrape_jgyl() -> None:
    out = RAW_DIR / "14_tcm_jgyl_chinese.txt"

    if out.exists() and out.stat().st_size > 20_000:
        log.info(f"[JGYL] File exists ({out.stat().st_size//1024}KB), skipping")
        return

    log.info("[JGYL] Fetching 金匱要略...")
    wt = fetch_wikitext("金匱要略")
    polite_sleep()

    if wt is None:
        log_missing("JGYL", "金匱要略", "Page not found on Wikisource")
        return

    text = wikitext_to_chinese(wt)
    cjk_count = len(CJK_RE.findall(text))

    # Split into chapters using the 【...】 section markers
    sections = re.split(r"\n\n【(.+?)】\n", text)
    # sections[0] = preamble, then alternating title/content
    header = "=== 金匱要略 ===\n\n來源：zh.wikisource.org\n\n"
    parts = [header]

    if len(sections) > 1:
        # preamble
        if sections[0].strip():
            parts.append(sections[0].strip() + "\n")
        # chapters
        for j in range(1, len(sections) - 1, 2):
            ch_title = sections[j].strip()
            ch_content = sections[j+1].strip() if j+1 < len(sections) else ""
            if ch_content and CJK_RE.search(ch_content):
                parts.append(f"\n\n=== {ch_title} ===\n\n{ch_content}\n")
    else:
        parts.append(text)

    out.write_text("".join(parts), encoding="utf-8")
    log.info(f"[JGYL] ✓ {cjk_count} CJK chars → {out} ({out.stat().st_size//1024}KB)")


# ══════════════════════════════════════════════════════════════════════════════
# Book 3: 難經 — single page, 81 difficulties
# ══════════════════════════════════════════════════════════════════════════════

def scrape_nanjing() -> None:
    out = RAW_DIR / "15_tcm_nanjing_chinese.txt"

    if out.exists() and out.stat().st_size > 10_000:
        log.info(f"[NanJing] File exists ({out.stat().st_size//1024}KB), skipping")
        return

    log.info("[NanJing] Fetching 難經...")
    wt = fetch_wikitext("難經")
    polite_sleep()

    if wt is None:
        log_missing("NanJing", "難經", "Page not found on Wikisource")
        return

    text = wikitext_to_chinese(wt)
    cjk_count = len(CJK_RE.findall(text))

    # Split into the 81 difficulties
    sections = re.split(r"\n\n【(第[一二三四五六七八九十百]+難)】\n", text)
    header = "=== 難經 ===\n\n來源：zh.wikisource.org\n\n"
    parts = [header]

    if len(sections) > 1:
        if sections[0].strip():
            parts.append(sections[0].strip() + "\n")
        for j in range(1, len(sections) - 1, 2):
            nan_title = sections[j].strip()
            nan_content = sections[j+1].strip() if j+1 < len(sections) else ""
            if nan_content:
                parts.append(f"\n\n=== {nan_title} ===\n\n{nan_content}\n")
    else:
        parts.append(text)

    out.write_text("".join(parts), encoding="utf-8")
    log.info(f"[NanJing] ✓ {cjk_count} CJK chars, {(len(sections)-1)//2} difficulties → {out} ({out.stat().st_size//1024}KB)")


# ══════════════════════════════════════════════════════════════════════════════
# Book 4: 本草綱目 — 66 category sections
# ══════════════════════════════════════════════════════════════════════════════

# Logical sort order for BCGM sections
BCGM_ORDER = [
    "序", "凡例", "序例上", "序例下", "百病主治藥上", "百病主治藥下", "主治",
    "水部", "火部", "土部",
    "金石之一", "金石之二", "金石之三", "金石之四", "金石之五",
    "草之一", "草之二", "草之三", "草之四", "草之五",
    "草之六", "草之七", "草之八", "草之九", "草之十", "雜草",
    "穀之一", "穀之二", "穀之三", "穀之四",
    "菜之一", "菜之二", "菜之三",
    "果之一", "果之二", "果之三", "果之四", "果之五", "果之六",
    "木之一", "木之二", "木之三", "木之四", "木之五", "木之六",
    "服器部",
    "蟲之一", "蟲之二", "蟲之三", "蟲之四",
    "鱗之一", "鱗之二", "鱗之三", "鱗之四",
    "介之一", "介之二",
    "禽之一", "禽之二", "禽之三", "禽之四",
    "獸之一", "獸之二", "獸之三", "獸之四",
    "人部", "名醫別錄",
]


def scrape_bcgm() -> None:
    out = RAW_DIR / "16_tcm_bcgm_chinese.txt"
    existing = parse_sections(out)

    # Discover all subpages
    log.info("[BCGM] Fetching subpage list...")
    all_subs = fetch_subpages("本草綱目/")
    polite_sleep()

    # Only direct 本草綱目/ subpages (not 四庫全書本 variant)
    direct = sorted(
        [p for p in all_subs if p.startswith("本草綱目/") and "(" not in p],
        key=lambda p: BCGM_ORDER.index(p.split("/", 1)[1])
        if p.split("/", 1)[1] in BCGM_ORDER else 999
    )

    log.info(f"[BCGM] {len(direct)} sections found")
    need = [(p, p.split("/", 1)[1]) for p in direct
            if not section_is_clean(existing.get(p.split("/", 1)[1], ""))]
    log.info(f"[BCGM] {len(direct)-len(need)} already clean, {len(need)} to fetch")

    if not out.exists():
        out.write_text("=== 本草綱目 ===\n\n來源：zh.wikisource.org\n", encoding="utf-8")

    for i, (ws_title, short_title) in enumerate(need, 1):
        log.info(f"[BCGM] {i}/{len(need)}: {short_title}")
        wt = fetch_wikitext(ws_title)
        polite_sleep()

        if wt is None:
            log_missing("BCGM", short_title, f"Page not found: {ws_title}")
            append_section(out, short_title, "[CHAPTER MISSING — not on Wikisource; fetch from ctext.org]")
            continue

        text = wikitext_to_chinese(wt)
        cjk_count = len(CJK_RE.findall(text))

        if cjk_count >= 80:
            append_section(out, short_title, text)
            log.info(f"  ✓ {cjk_count} CJK chars")
        else:
            log_missing("BCGM", short_title, f"Sparse: only {cjk_count} CJK chars")
            append_section(out, short_title, f"[SPARSE — {cjk_count} CJK chars]\n\n{text}")

    size_kb = out.stat().st_size // 1024
    log.info(f"[BCGM] Done → {out} ({size_kb}KB)")


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    log.info("=" * 60)
    log.info("Wikisource Scraper — Daoist Medical Canon START")
    log.info("=" * 60)

    for label, fn in [
        ("BOOK 1/4: 黃帝內經 (Huangdi Neijing)", scrape_hdnj),
        ("BOOK 2/4: 金匱要略 (Jingui Yaolue)",    scrape_jgyl),
        ("BOOK 3/4: 難經 (Nan Jing)",              scrape_nanjing),
        ("BOOK 4/4: 本草綱目 (Bencao Gangmu)",     scrape_bcgm),
    ]:
        log.info(f"\n>>> {label}")
        try:
            fn()
        except Exception as exc:
            log.error(f"  {label} crashed: {exc}", exc_info=True)
        time.sleep(5)

    write_missing_report()

    log.info("\n" + "=" * 60)
    log.info("ALL DONE")
    log.info("=" * 60)

    # Final summary
    for fname, label in [
        ("13_tcm_hdnj_chinese.txt",    "HDNJ"),
        ("14_tcm_jgyl_chinese.txt",    "JGYL"),
        ("15_tcm_nanjing_chinese.txt", "NanJing"),
        ("16_tcm_bcgm_chinese.txt",    "BCGM"),
    ]:
        p = RAW_DIR / fname
        if p.exists():
            secs = len(re.findall(r"^=== .+ ===$", p.read_text(encoding="utf-8"), re.MULTILINE))
            log.info(f"  {label}: {p.stat().st_size//1024}KB, {secs} sections  ✓")
        else:
            log.info(f"  {label}: NOT CREATED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
