#!/usr/bin/env python3
"""
Phase 1 ETL: Scrape Legge I Ching hexagrams from sacred-texts.com.
Downloads ic01.htm through ic64.htm, extracts core text + commentary, saves to
data/chunked/04_confucian_legge/hex_01.txt ... hex_64.txt.
"""
import argparse
import re
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://web.archive.org/web/20240227000000/https://sacred-texts.com/ich/ic{:02d}.htm"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 5


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_main_content(soup: BeautifulSoup) -> str:
    """Extract main text from sacred-texts page. Prefer center content table cell."""
    # Sacred-texts uses table layout; main content is typically in a td with "HEXAGRAM"
    tds = soup.find_all("td")
    candidates = []
    for td in tds:
        text = td.get_text(separator="\n", strip=True)
        if "HEXAGRAM" in text.upper() and len(text) > 200:
            candidates.append((len(text), text))
    if candidates:
        candidates.sort(key=lambda x: -x[0])
        return candidates[0][1]
    # Fallback: use body text
    body = soup.find("body")
    if body:
        return body.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


def clean_text(raw: str) -> str:
    """Strip header nav, footer, and boilerplate. Keep hexagram content + footnotes."""
    lines = raw.split("\n")
    out = []
    in_content = False
    skip_nav = re.compile(
        r"^\s*\[?(Sacred Texts|Index|Previous|Next)\]?\s*$",
        re.IGNORECASE,
    )
    next_footer = re.compile(
        r"^\s*\[?Next:\s*.+Hexagram\]?\s*.*$",
        re.IGNORECASE,
    )
    archive_title = re.compile(
        r".*Internet Sacred Text Archive.*",
        re.IGNORECASE,
    )
    wayback_boilerplate = re.compile(
        r"^\d+\s+captures$|^\d{1,2}$|^About this capture$|^COLLECTED BY$|"
        r"^Collection:$|^Save Page Now|^TIMESTAMPS$|^The Wayback Machine\s*-|^Outlinks$|"
        r"^\d{1,2}\s+\w+\s+\d{4}\s*-\s*\d{1,2}\s+\w+\s+\d{4}$|"
        r"^(Mar|APR|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|success|fail|\d{4})$",
        re.IGNORECASE,
    )

    for line in lines:
        stripped = line.strip()
        # Skip pure separators at start
        if not in_content:
            if stripped in ("", "---"):
                continue
            if (
                archive_title.match(stripped)
                or skip_nav.match(stripped)
                or wayback_boilerplate.match(stripped)
            ):
                continue
            # First real content
            in_content = True

        # Skip footer "[Next: N. The X Hexagram](url)"
        if next_footer.match(stripped):
            break
        # Skip standalone "---" at end (often after footer)
        if stripped == "---" and out and out[-1].strip() == "":
            continue
        # Skip nav link lines that slipped through
        if stripped and skip_nav.match(stripped):
            continue

        out.append(line)

    # Trim trailing empty lines and normalize internal whitespace
    while out and out[-1].strip() == "":
        out.pop()
    return "\n".join(out)


def scrape_hexagram(num: int, limit: int | None) -> str | None:
    """Fetch and clean one hexagram page. Returns clean text or None if limit reached."""
    if limit is not None and num > limit:
        return None
    url = BASE_URL.format(num)
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                raise
    resp.encoding = resp.apparent_encoding or "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")
    raw = find_main_content(soup)
    return clean_text(raw)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scrape Legge I Ching hexagrams from sacred-texts.com."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit to first N hexagrams (0 = all 64).",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=1,
        help="Start from hexagram N (for resuming).",
    )
    args = parser.parse_args()
    limit = args.limit if args.limit > 0 else None
    start = max(1, args.start)

    root = project_root()
    out_dir = root / "data" / "chunked" / "04_confucian_legge"
    out_dir.mkdir(parents=True, exist_ok=True)

    for i in range(start, 65):
        if limit and i > limit:
            break
        try:
            text = scrape_hexagram(i, limit)
            if text is None:
                break
            out_path = out_dir / f"hex_{i:02d}.txt"
            out_path.write_text(text, encoding="utf-8")
            print(f"Saved {out_path.name}", file=sys.stderr)
        except Exception as e:
            print(f"Error fetching hexagram {i}: {e}", file=sys.stderr)
            raise
        time.sleep(1)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
