#!/usr/bin/env python3
"""
Scrape classical Chinese medical texts from ctext.org.
Targets: Shennong Bencao Jing (Wiki format), Huangdi Neijing (Standard format).
Set-it-and-forget-it scraper with anti-bot headers, polite delays, and iterative saving.
"""
import argparse
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

# Anti-bot headers (robust browser simulation)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

REQUEST_TIMEOUT = 60
ERROR_WAIT = 10  # seconds to wait after a failed request
SLEEP_MIN, SLEEP_MAX = 4, 8  # randomized delay between EVERY page request

# CJK character range for filtering Chinese text
CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")

# Boilerplate to skip when extracting
SKIP_PHRASES = [
    "Chinese Text Project",
    "Log in",
    "Search",
    "Jump to dictionary",
    "Show parallel",
    "Please help",
    "copyright",
]


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def polite_sleep() -> None:
    """Randomized delay between 4–8 seconds (anti-ban)."""
    delay = random.uniform(SLEEP_MIN, SLEEP_MAX)
    time.sleep(delay)


def fetch(url: str, use_gb: bool = False) -> requests.Response:
    """Fetch URL with anti-bot headers. Optionally switch to Chinese (gb) interface."""
    if use_gb:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query)
        qs["if"] = ["gb"]
        new_query = "&".join(f"{k}={v[0]}" for k, v in qs.items())
        url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}?{new_query}" if new_query else url
    resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    return resp


def extract_chinese_from_soup(soup: BeautifulSoup) -> str:
    """
    Extract Chinese text from ctext.org HTML.
    Tries: td.ctext, #content div, table cells with CJK.
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
                if any(p in text for p in SKIP_PHRASES):
                    continue
                paragraphs.append(text)

    # 3. Wiki/table format: rows with Chinese
    if not paragraphs:
        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                for td in tr.find_all("td"):
                    text = td.get_text(separator=" ", strip=True)
                    if text and CJK_RE.search(text) and len(text) > 3:
                        if any(p in text for p in SKIP_PHRASES):
                            continue
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


# ---------------------------------------------------------------------------
# Shennong Bencao Jing (Wiki format)
# ---------------------------------------------------------------------------

SNBCJ_TOC_URL = "https://ctext.org/wiki.pl?if=en&res=580853"
SNBCJ_OUT = "12_tcm_snbcj_chinese.txt"


def get_snbcj_chapter_links(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
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


def scrape_snbcj(raw_dir: Path) -> None:
    """Scrape 神農本草經 (Shennong Bencao Jing). Wiki format."""
    out_path = raw_dir / SNBCJ_OUT
    # Truncate file at start (fresh run)
    out_path.write_text("", encoding="utf-8")

    print("[SNBCJ] Fetching TOC...", flush=True)
    try:
        resp = fetch(SNBCJ_TOC_URL)
    except Exception as e:
        print(f"[SNBCJ] ERROR fetching TOC: {e}", flush=True)
        time.sleep(ERROR_WAIT)
        return
    polite_sleep()

    soup = BeautifulSoup(resp.text, "html.parser")
    chapters = get_snbcj_chapter_links(soup, SNBCJ_TOC_URL)

    if not chapters:
        # Fallback: main chapter 10407
        chapters = [
            ("https://ctext.org/wiki.pl?if=gb&chapter=10407", "神農本草經"),
        ]
        print("[SNBCJ] TOC empty, using fallback chapter", flush=True)

    total = len(chapters)
    for i, (url, title) in enumerate(chapters, 1):
        print(f"[SNBCJ] Chapter {i}/{total}: {title}", flush=True)
        try:
            resp = fetch(url, use_gb=True)
            soup = BeautifulSoup(resp.text, "html.parser")
            text = extract_chinese_from_soup(soup)
            if text:
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n=== {title} ===\n\n")
                    f.write(text)
                    f.write("\n\n")
                print(f"  -> Saved {len(text)} chars", flush=True)
            else:
                print("  -> No Chinese text extracted", flush=True)
        except Exception as e:
            print(f"  -> ERROR: {e}", flush=True)
            time.sleep(ERROR_WAIT)
        if i < total:
            polite_sleep()

    print(f"[SNBCJ] Done. Output: {out_path}", flush=True)


# ---------------------------------------------------------------------------
# Huangdi Neijing (Standard format)
# ---------------------------------------------------------------------------

HDNJ_TOC_URL = "https://ctext.org/huangdi-neijing"
HDNJ_OUT = "13_tcm_hdnj_chinese.txt"
HDNJ_SKIP_SLUGS = {"suwen", "ling-shu-jing", "ens", "zh", "huangdi-neijing"}  # Section indexes, language switchers, base


def get_hdnj_chapter_links(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """Extract chapter links from TOC. Standard format: /huangdi-neijing/{slug}."""
    seen = set()
    links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        # Match both "/huangdi-neijing/slug" and "huangdi-neijing/slug" (relative)
        if "huangdi-neijing" not in href or "huangdi-neijing/huangdi-neijing" in href:
            continue
        if any(x in href for x in ("library", "search", "discuss", ".pl")):
            continue
        full_url = urljoin("https://ctext.org", href)
        parsed = urlparse(full_url)
        path = parsed.path.strip("/")
        parts = path.split("/")
        if len(parts) >= 2:
            slug = parts[1]
        elif len(parts) == 1:
            slug = parts[0]
        else:
            continue
        if slug in HDNJ_SKIP_SLUGS or "." in slug:
            continue
        if slug not in seen:
            seen.add(slug)
            title = a.get_text(strip=True) or slug
            links.append((full_url, title))
    return links


def scrape_hdnj(raw_dir: Path, limit: int | None = None) -> None:
    """Scrape 黃帝內經 (Huangdi Neijing). Standard format with Suwen + Ling Shu Jing."""
    out_path = raw_dir / HDNJ_OUT
    out_path.write_text("", encoding="utf-8")

    print("[HDNJ] Fetching TOC...", flush=True)
    try:
        resp = fetch(HDNJ_TOC_URL)
    except Exception as e:
        print(f"[HDNJ] ERROR fetching TOC: {e}", flush=True)
        time.sleep(ERROR_WAIT)
        return
    polite_sleep()

    soup = BeautifulSoup(resp.text, "html.parser")
    chapters = get_hdnj_chapter_links(soup)
    if limit:
        chapters = chapters[:limit]
        print(f"[HDNJ] Limiting to first {limit} chapters", flush=True)
    total = len(chapters)
    print(f"[HDNJ] Found {total} chapters", flush=True)

    for i, (url, title) in enumerate(chapters, 1):
        print(f"[HDNJ] Chapter {i}/{total}: {title[:40]}...", flush=True)
        try:
            # Prefer Chinese version for HDNJ
            zh_url = url.rstrip("/") + "/zh" if "/zh" not in url and "/ens" not in url else url
            resp = fetch(zh_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            text = extract_chinese_from_soup(soup)
            if not text:
                # Fallback to default (may have Chinese in table)
                resp = fetch(url)
                soup = BeautifulSoup(resp.text, "html.parser")
                text = extract_chinese_from_soup(soup)
            if text:
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(f"\n\n=== {title} ===\n\n")
                    f.write(text)
                    f.write("\n\n")
                print(f"  -> Saved {len(text)} chars", flush=True)
            else:
                print("  -> No Chinese text extracted", flush=True)
        except Exception as e:
            print(f"  -> ERROR: {e}", flush=True)
            time.sleep(ERROR_WAIT)
        if i < total:
            polite_sleep()

    print(f"[HDNJ] Done. Output: {out_path}", flush=True)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description="Scrape SNBCJ and HDNJ from ctext.org")
    parser.add_argument("--book", choices=["snbcj", "hdnj", "all"], default="all", help="Which book(s) to scrape")
    parser.add_argument("--limit", type=int, default=0, help="For HDNJ only: limit to first N chapters (0=all)")
    args = parser.parse_args()

    root = project_root()
    raw_dir = root / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] data/raw exists: {raw_dir}", flush=True)

    if args.book in ("snbcj", "all"):
        print("\n=== Shennong Bencao Jing (神農本草經) ===", flush=True)
        scrape_snbcj(raw_dir)

    if args.book in ("hdnj", "all"):
        print("\n=== Huangdi Neijing (黃帝內經) ===", flush=True)
        scrape_hdnj(raw_dir, limit=args.limit if args.limit > 0 else None)

    print("\n=== All done ===", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
