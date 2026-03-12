#!/usr/bin/env python3
"""
Scrape classical Chinese medical texts from ctext.org for TCM Materia Medica.
Targets: Shennong Bencao Jing, Shanghan Lun, Bencao Gangmu.
Uses requests + BeautifulSoup with anti-bot headers and polite delays.
"""
import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

# Anti-bot headers (required or ctext.org blocks the connection)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 5
POLITENESS_DELAY = 3  # seconds between page requests

# Book targets
TARGETS = {
    "snbcj": {
        "name": "Shennong Bencao Jing",
        "url": "https://ctext.org/wiki.pl?if=en&res=580853",
        "out_file": "09_tcm_snbcj_chinese.txt",
    },
    "shl": {
        "name": "Shanghan Lun",
        "url": "https://ctext.org/shang-han-lun",
        "out_file": "10_tcm_shl_chinese.txt",
    },
    "bcgm": {
        "name": "Bencao Gangmu",
        "url": "https://ctext.org/wiki.pl?if=en&res=8",
        "out_file": "11_tcm_bcgm_chinese.txt",
    },
}

# CJK character range for filtering Chinese text
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def fetch(url: str, use_gb: bool = False) -> requests.Response:
    """Fetch URL with anti-bot headers. Optionally switch to Chinese (gb) interface."""
    if use_gb:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        qs["if"] = ["gb"]
        new_query = "&".join(f"{k}={v[0]}" for k, v in qs.items())
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}" if new_query else url
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or "utf-8"
            return resp
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise e


def fetch_api(urn: str) -> dict | None:
    """Fetch text from ctext.org API. Returns JSON with fulltext array or None."""
    api_url = f"https://api.ctext.org/gettext?urn={urn}"
    try:
        resp = requests.get(api_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def extract_chinese_from_soup(soup: BeautifulSoup) -> str:
    """
    Extract Chinese text from ctext.org HTML.
    Tries: td.ctext, #content, table cells with CJK, main content divs.
    """
    paragraphs = []

    # 1. td.ctext (primary container for Chinese text)
    for td in soup.find_all("td", class_="ctext"):
        text = td.get_text(separator=" ", strip=True)
        if text and CJK_RE.search(text):
            paragraphs.append(text)

    # 2. #content div
    content = soup.find(id="content")
    if content and not paragraphs:
        for elem in content.find_all(["p", "td", "div"], recursive=True):
            text = elem.get_text(separator=" ", strip=True)
            if text and len(text) > 5 and CJK_RE.search(text):
                # Skip nav/footer boilerplate
                if any(
                    x in text
                    for x in [
                        "Chinese Text Project",
                        "Log in",
                        "Search",
                        "Jump to dictionary",
                        "Show parallel",
                        "Please help",
                        "copyright",
                    ]
                ):
                    continue
                paragraphs.append(text)

    # 3. Wiki table format: rows with | num | chinese text |
    if not paragraphs:
        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                cells = tr.find_all("td")
                for td in cells:
                    text = td.get_text(separator=" ", strip=True)
                    if text and CJK_RE.search(text) and len(text) > 3:
                        paragraphs.append(text)

    # 4. Any td with substantial Chinese
    if not paragraphs:
        for td in soup.find_all("td"):
            text = td.get_text(separator=" ", strip=True)
            if text and len(text) > 10 and CJK_RE.search(text):
                if "Chinese Text Project" not in text and "http" not in text:
                    paragraphs.append(text)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for p in paragraphs:
        p_clean = p.strip()
        if p_clean and p_clean not in seen:
            seen.add(p_clean)
            unique.append(p_clean)

    return "\n\n".join(unique) if unique else ""


def get_wiki_chapter_links(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
    """Extract wiki chapter links (url, title) from TOC. Deduplicates by chapter ID."""
    links = []
    seen_chapters = set()
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "chapter=" in href:
            full_url = urljoin(base_url, href)
            parsed = urlparse(full_url)
            qs = parse_qs(parsed.query)
            ch = qs.get("chapter", [None])[0]
            if ch and ch not in seen_chapters:
                seen_chapters.add(ch)
                title = a.get_text(strip=True) or f"chapter_{ch}"
                links.append((full_url, title))
    return links


def scrape_shennong_bencao_jing(base_url: str) -> str:
    """Scrape 神農本草經 (Shennong Bencao Jing). Single main chapter + anchors."""
    print("[SNBCJ] Fetching main TOC...", file=sys.stderr)
    resp = fetch(base_url)
    time.sleep(POLITENESS_DELAY)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find main content link (神農本草經 with chapter=10407)
    chapter_url = None
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "chapter=10407" in href:
            chapter_url = urljoin(base_url, href)
            break

    if not chapter_url:
        # Fallback: try direct chapter URL
        chapter_url = "https://ctext.org/wiki.pl?if=gb&chapter=10407"

    print(f"[SNBCJ] Fetching chapter: {chapter_url}", file=sys.stderr)
    resp = fetch(chapter_url, use_gb=True)
    soup = BeautifulSoup(resp.text, "html.parser")
    text = extract_chinese_from_soup(soup)

    # API fallback for cleaner text
    if len(text) < 500:
        print("[SNBCJ] HTML extraction sparse, trying API...", file=sys.stderr)
        data = fetch_api("ctp:ws10407")
        if data and "fulltext" in data:
            text = "\n\n".join(data["fulltext"])
            print(f"[SNBCJ] API returned {len(data['fulltext'])} paragraphs", file=sys.stderr)

    return text


# Known Shanghan Lun chapter slugs (fallback if TOC parsing fails)
SHANGHAN_LUN_SLUGS = [
    "bian-mai-fa",
    "ping-mai-fa",
    "shang-han-li",
    "bian-chi-shi-he-mai-zheng",
    "bian-tai-yang-bing-mai-zheng",
    "bian-tai-yang-bing-mai-zheng1",
    "bian-tai-yang-mai-zheng-bing",
    "bian-yang-ming-mai-zheng-bing-zhi",
    "bian-shao-yang-bing-mai-zheng",
    "bian-tai-yin-mai-zheng-bing-zhi",
    "bian-shao-yin-bing-mai-zheng",
    "bian-jue-yin-bing-mai-zheng",
    "bian-huo-luan-bing-mai-zheng",
    "bian-yin-yang-yi-cha-hou",
    "bian-bu-ke-fa-han-bing",
    "bian-ke-fa-han-zheng-bing-zhi",
    "bian-fa-han-hou-bing-mai",
    "bian-bu-ke-tu",
    "bian-ke-tu",
    "bian-bu-ke-xia-bing-mai",
    "bian-ke-xia-bing-mai-zheng",
    "bian-fa-han-tu-xia-hou",
]


def scrape_shanghan_lun(base_url: str) -> str:
    """Scrape 傷寒論 (Shanghan Lun). Standard format with multiple chapters."""
    print("[SHL] Fetching TOC...", file=sys.stderr)
    resp = fetch(base_url)
    time.sleep(POLITENESS_DELAY)
    soup = BeautifulSoup(resp.text, "html.parser")

    # Find chapter links in Media section: /shang-han-lun/bian-mai-fa etc.
    chapter_links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if "shang-han-lun/" in href:
            full_url = urljoin("https://ctext.org", href)
            path = urlparse(full_url).path
            parts = path.strip("/").split("/")
            # Want /shang-han-lun/{slug} - skip library.pl, search.pl, ens, zh, etc.
            slug = parts[1]
            if (
                len(parts) >= 2
                and parts[0] == "shang-han-lun"
                and "." not in slug
                and slug not in ("ens", "zh")  # language switchers
            ):
                chapter_links.append((full_url, slug))

    # Deduplicate by slug, preserving order
    seen = set()
    unique = []
    for url, slug in chapter_links:
        if slug not in seen:
            seen.add(slug)
            unique.append((url, slug))

    # Fallback to known slugs if TOC parsing found nothing
    if not unique:
        print("[SHL] TOC parsing found no chapters, using fallback list", file=sys.stderr)
        unique = [
            (f"https://ctext.org/shang-han-lun/{slug}", slug)
            for slug in SHANGHAN_LUN_SLUGS
        ]

    all_text = []
    for i, (url, slug) in enumerate(unique):
        print(f"[SHL] Chapter {i + 1}/{len(unique)}: {slug}", file=sys.stderr)
        # Prefer API for Shanghan Lun (HTML often shows English translation)
        urn = f"ctp:shang-han-lun/{slug}"
        data = fetch_api(urn)
        if data and "fulltext" in data:
            all_text.extend(data["fulltext"])
            print(f"  -> API: {len(data['fulltext'])} paragraphs", file=sys.stderr)
        else:
            resp = fetch(url, use_gb=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            text = extract_chinese_from_soup(soup)
            if text:
                all_text.append(text)
                print(f"  -> HTML: {len(text)} chars", file=sys.stderr)
        time.sleep(POLITENESS_DELAY)

    return "\n\n".join(all_text)


def scrape_bencao_gangmu(base_url: str, limit: int | None = None) -> str:
    """Scrape 本草綱目 (Bencao Gangmu). Wiki format with many chapters."""
    print("[BCGM] Fetching TOC...", file=sys.stderr)
    resp = fetch(base_url)
    time.sleep(POLITENESS_DELAY)
    soup = BeautifulSoup(resp.text, "html.parser")

    chapters = get_wiki_chapter_links(soup, base_url)
    # Filter to top-level chapters only (avoid anchor duplicates)
    seen_ids = set()
    top_level = []
    for url, title in chapters:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        ch = qs.get("chapter", [None])[0]
        if ch and ch not in seen_ids:
            seen_ids.add(ch)
            top_level.append((url, title, ch))

    if limit:
        top_level = top_level[:limit]
        print(f"[BCGM] Limiting to first {limit} chapters", file=sys.stderr)

    all_text = []
    for i, (url, title, ch_id) in enumerate(top_level):
        print(f"[BCGM] Chapter {i + 1}/{len(top_level)}: {title} (id={ch_id})", file=sys.stderr)
        # Try API first
        urn = f"ctp:ws{ch_id}"
        data = fetch_api(urn)
        if data and "fulltext" in data:
            all_text.extend(data["fulltext"])
            print(f"  -> API: {len(data['fulltext'])} paragraphs", file=sys.stderr)
        else:
            resp = fetch(url, use_gb=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            text = extract_chinese_from_soup(soup)
            if text:
                all_text.append(text)
                print(f"  -> HTML: {len(text)} chars", file=sys.stderr)
        time.sleep(POLITENESS_DELAY)

    return "\n\n".join(all_text)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scrape TCM texts from ctext.org (Shennong Bencao Jing, Shanghan Lun, Bencao Gangmu)."
    )
    parser.add_argument(
        "--book",
        choices=["snbcj", "shl", "bcgm", "all"],
        default="all",
        help="Which book to scrape (default: all)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="For Bencao Gangmu only: limit to first N chapters (0 = all)",
    )
    args = parser.parse_args()

    root = project_root()
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    books = ["snbcj", "shl", "bcgm"] if args.book == "all" else [args.book]
    limit = args.limit if args.limit > 0 else None

    for key in books:
        cfg = TARGETS[key]
        print(f"\n=== {cfg['name']} ===", file=sys.stderr)
        try:
            if key == "snbcj":
                text = scrape_shennong_bencao_jing(cfg["url"])
            elif key == "shl":
                text = scrape_shanghan_lun(cfg["url"])
            else:
                text = scrape_bencao_gangmu(cfg["url"], limit=limit)

            out_path = raw_dir / cfg["out_file"]
            out_path.write_text(text, encoding="utf-8")
            print(f"Saved {len(text):,} chars to {out_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error scraping {cfg['name']}: {e}", file=sys.stderr)
            raise

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
