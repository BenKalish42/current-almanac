#!/usr/bin/env python3
"""Clean XTTS fine-tune dataset: drop silent/near-silent WAVs, missing files, text > max chars."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import librosa
import numpy as np
import pandas as pd


def row_wav_path(dataset_dir: Path, audio_file: str) -> Path:
    p = Path(audio_file)
    return p if p.is_absolute() else dataset_dir / p


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dataset-dir", type=Path, required=True)
    p.add_argument("--max-text-chars", type=int, default=250)
    p.add_argument("--rms-threshold", type=float, default=1e-4)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    ds = args.dataset_dir.expanduser().resolve()
    for name in ("metadata_train.csv", "metadata_eval.csv"):
        path = ds / name
        if not path.is_file():
            print(f"Skip missing {path}", file=sys.stderr)
            continue

        df = pd.read_csv(path, sep="|")
        before = len(df)
        drop_reasons: list[str] = []

        def audit(row) -> str | None:
            rel = str(row["audio_file"])
            text = str(row.get("text", ""))
            wav = row_wav_path(ds, rel)
            if len(text) > args.max_text_chars:
                return "long_text"
            if not wav.is_file():
                return "missing_file"
            try:
                y, sr = librosa.load(str(wav), sr=None, mono=True)
                dur = len(y) / sr
                rms = float(np.sqrt(np.mean(np.square(y))) if len(y) else 0.0)
                if rms < args.rms_threshold or dur < 0.05:
                    return "silent_or_tiny"
            except Exception:
                return "load_error"
            return None

        reasons = df.apply(audit, axis=1)
        bad_mask = reasons.notna()
        n_bad = int(bad_mask.sum())
        if n_bad:
            print(f"{name}: drop {n_bad} / {before} rows", file=sys.stderr)
            vc = reasons[bad_mask].value_counts()
            print(vc.to_string(), file=sys.stderr)

        df_clean = df.loc[~bad_mask].copy()
        after = len(df_clean)
        if after < 1:
            print(f"ERROR: {name} would be empty", file=sys.stderr)
            return 1

        if not args.dry_run:
            df_clean.to_csv(path, sep="|", index=False)
            print(f"{name}: {before} -> {after} rows (wrote {path})", file=sys.stderr)
        else:
            print(f"{name}: {before} -> {after} rows (dry-run)", file=sys.stderr)

    # Remove WAV files no longer referenced in train+eval
    if not args.dry_run:
        referenced: set[Path] = set()
        for name in ("metadata_train.csv", "metadata_eval.csv"):
            path = ds / name
            if not path.is_file():
                continue
            df = pd.read_csv(path, sep="|")
            for _, r in df.iterrows():
                referenced.add(row_wav_path(ds, str(r["audio_file"])).resolve())
        wav_dir = ds / "wavs"
        if wav_dir.is_dir():
            removed = 0
            for w in wav_dir.glob("*.wav"):
                if w.resolve() not in referenced:
                    w.unlink(missing_ok=True)
                    removed += 1
            if removed:
                print(f"Removed {removed} unreferenced .wav under wavs/", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
