#!/usr/bin/env python3
"""
Slice a long recording into multiple WAV clips for XTTS reference speakers.

XTTS v2 conditions on reference audio; Coqui accepts a list of files and
merges latents. Spread segments across the file (speech from different
parts of the recording) for stabler cloning than a single random cut.

Requires: ffmpeg (brew install ffmpeg)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def ffprobe_duration_sec(path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(path),
    ]
    out = subprocess.check_output(cmd, text=True)
    data = json.loads(out)
    return float(data["format"]["duration"])


def extract_clip(src: Path, dst: Path, start_sec: float, duration_sec: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-ss",
        str(max(0.0, start_sec)),
        "-i",
        str(src),
        "-t",
        str(duration_sec),
        "-ar",
        "24000",
        "-ac",
        "1",
        "-sample_fmt",
        "s16",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def main() -> int:
    p = argparse.ArgumentParser(description="Build XTTS reference WAV clips from one long file")
    p.add_argument(
        "input_audio",
        type=Path,
        nargs="?",
        default=Path("/Users/benjaminkalish/Music/TomTraining.mp3"),
        help="Source recording (e.g. MP3)",
    )
    p.add_argument(
        "-o",
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "reference_clips",
        help="Directory for clip_001.wav, ...",
    )
    p.add_argument("--count", type=int, default=12, help="Number of clips")
    p.add_argument("--segment-sec", type=float, default=20.0, help="Length of each clip")
    p.add_argument(
        "--margin-sec",
        type=float,
        default=45.0,
        help="Skip this many seconds at start and end of the file when placing clips",
    )
    args = p.parse_args()

    src = args.input_audio.expanduser().resolve()
    if not src.is_file():
        print(f"ERROR: Input not found: {src}", file=sys.stderr)
        return 1

    duration = ffprobe_duration_sec(src)
    if duration <= args.margin_sec * 2 + args.segment_sec:
        print("ERROR: File too short for margin + segment length.", file=sys.stderr)
        return 1

    usable = duration - 2 * args.margin_sec
    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    n = max(1, args.count)
    for i in range(n):
        t0 = args.margin_sec + (usable - args.segment_sec) * (i / max(1, n - 1))
        dst = out_dir / f"clip_{i + 1:03d}.wav"
        extract_clip(src, dst, t0, args.segment_sec)
        print(f"Wrote {dst} (from {t0:.1f}s)")

    print(f"\nDone. Use --clips-dir {out_dir} with xtts_conversation.py", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
