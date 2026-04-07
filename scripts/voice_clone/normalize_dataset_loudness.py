#!/usr/bin/env python3
"""
Per-file loudness normalization for an existing XTTS dataset (WAVs referenced in metadata CSVs).

Uses a simple integrated-LUFS target (EBU-style via pyloudnorm). Clips are scaled in float,
then saved as PCM_16 with a light peak ceiling to avoid clipping.

  pip install pyloudnorm soundfile
  python scripts/voice_clone/normalize_dataset_loudness.py \\
      --dataset-dir scripts/voice_clone/xtts_ft_output/dataset \\
      --target-lufs -18
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf

try:
    import pyloudnorm as pyln
except ImportError:
    print("Install: pip install pyloudnorm soundfile", file=sys.stderr)
    raise


def wav_path(dataset_dir: Path, rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else dataset_dir / p


def normalize_file(path: Path, target: float, peak_ceiling: float) -> str | None:
    data, rate = sf.read(str(path), always_2d=True, dtype="float64")
    if data.shape[0] < int(0.3 * rate):
        return "skip_short"
    meter = pyln.Meter(rate)
    try:
        loudness = meter.integrated_loudness(data)
    except Exception:
        return "skip_meter"
    if not np.isfinite(loudness):
        return "skip_nan"
    # Silence-ish: don't blow up gain
    if loudness < -70:
        return "skip_quiet"
    normed = pyln.normalize.loudness(data, loudness, target)
    peak = float(np.max(np.abs(normed)))
    if peak > peak_ceiling:
        normed = normed * (peak_ceiling / peak)
    sf.write(str(path), normed, rate, subtype="PCM_16")
    return None


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-dir", type=Path, required=True)
    p.add_argument("--target-lufs", type=float, default=-18.0)
    p.add_argument("--peak-ceiling", type=float, default=0.989, help="Linear peak cap (~ -0.1 dBFS)")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    ds = args.dataset_dir.expanduser().resolve()
    paths: set[Path] = set()
    for name in ("metadata_train.csv", "metadata_eval.csv"):
        csv = ds / name
        if not csv.is_file():
            continue
        df = pd.read_csv(csv, sep="|")
        for rel in df["audio_file"].astype(str):
            paths.add(wav_path(ds, rel).resolve())

    err = 0
    skipped: dict[str, int] = {}
    for path in sorted(paths):
        if not path.is_file():
            print(f"missing {path}", file=sys.stderr)
            err += 1
            continue
        if args.dry_run:
            continue
        reason = normalize_file(path, args.target_lufs, args.peak_ceiling)
        if reason:
            skipped[reason] = skipped.get(reason, 0) + 1
    print(
        f"Processed {len(paths)} paths under {ds} (target {args.target_lufs} LUFS, peak <= {args.peak_ceiling})",
        file=sys.stderr,
    )
    if skipped:
        print(f"Skipped: {skipped}", file=sys.stderr)
    return 1 if err else 0


if __name__ == "__main__":
    raise SystemExit(main())
