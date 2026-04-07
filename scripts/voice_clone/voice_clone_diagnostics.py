#!/usr/bin/env python3
"""
Measure *actionable* signals for XTTS fine-tune / clone quality (not a full MOS benchmark).

There is no single automatic score that equals “sounds better” — listeners and MOS studies are
the gold standard. This script reports:

  • Dataset health: silent/near-silent WAVs, duration spread, transcript length (Whisper issues).
  • Cheap acoustic match: MFCC embedding cosine similarity between a reference clip and a
    synthesis WAV (higher often correlates with “same speaker,” but is imperfect).

Usage:
  python3 scripts/voice_clone/voice_clone_diagnostics.py \\
      --dataset-dir scripts/voice_clone/xtts_ft_output/dataset

  python3 scripts/voice_clone/voice_clone_diagnostics.py \\
      --dataset-dir scripts/voice_clone/xtts_ft_output/dataset \\
      --ref-wav scripts/voice_clone/xtts_lambda_model/speaker_ref.wav \\
      --synth-wav scripts/voice_clone/outputs/xtts_test_capitalist_pig.wav
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import librosa
import numpy as np
import pandas as pd
from numpy.typing import NDArray


def _mfcc_mean_embedding(y: NDArray[np.float32], sr: int, n_mfcc: int = 20, max_sec: float = 3.0) -> NDArray[np.float32]:
    n = int(sr * max_sec)
    if len(y) > n:
        y = y[:n]
    y = librosa.effects.trim(y, top_db=35)[0]
    if len(y) < sr * 0.15:
        y = np.pad(y, (0, max(0, int(sr * 0.15) - len(y))), mode="constant")
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    v = mfcc.mean(axis=1).astype(np.float32)
    n = np.linalg.norm(v)
    if n > 1e-8:
        v = v / n
    return v


def cosine_sim(a: NDArray[np.float32], b: NDArray[np.float32]) -> float:
    return float(np.clip(np.dot(a, b), -1.0, 1.0))


def load_mono(path: str, target_sr: int) -> tuple[NDArray[np.float32], int]:
    y, sr = librosa.load(path, sr=target_sr, mono=True)
    return y.astype(np.float32), target_sr


def main() -> int:
    p = argparse.ArgumentParser(description="Voice clone / fine-tune diagnostics (dataset + optional ref vs synth)")
    p.add_argument("--dataset-dir", type=Path, required=True, help="Folder with metadata_train.csv and wavs/")
    p.add_argument("--ref-wav", type=Path, default=None, help="Reference speaker clip (e.g. fine-tune ref)")
    p.add_argument("--synth-wav", type=Path, default=None, help="Synthesized WAV to compare to ref")
    p.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    args = p.parse_args()

    ds = args.dataset_dir.expanduser().resolve()
    train_csv = ds / "metadata_train.csv"
    wav_dir = ds / "wavs"
    if not train_csv.is_file():
        print(f"Missing {train_csv}", file=sys.stderr)
        return 1
    if not wav_dir.is_dir():
        print(f"Missing {wav_dir}", file=sys.stderr)
        return 1

    df = pd.read_csv(train_csv, sep="|")
    rows_out: list[dict] = []
    durs: list[float] = []
    rms_list: list[float] = []
    bad_files: list[str] = []
    text_lens = df["text"].astype(str).str.len()

    for _, row in df.iterrows():
        rel = str(row["audio_file"])
        wav_path = ds / rel if not os.path.isabs(rel) else Path(rel)
        if not wav_path.is_file():
            bad_files.append(f"missing_file:{rel}")
            continue
        try:
            y, sr = librosa.load(str(wav_path), sr=None, mono=True)
            dur = float(len(y) / sr)
            rms = float(np.sqrt(np.mean(np.square(y))) if len(y) else 0.0)
            durs.append(dur)
            rms_list.append(rms)
            if rms < 1e-4 or dur < 0.05:
                bad_files.append(f"silent_or_tiny:{rel} rms={rms:.2e} dur={dur:.3f}s")
        except Exception as e:
            bad_files.append(f"load_error:{rel} {e}")

    report: dict = {
        "dataset_dir": str(ds),
        "train_rows_csv": int(len(df)),
        "wavs_scanned": len(durs),
        "duration_sec": {
            "mean": float(np.mean(durs)) if durs else None,
            "p10": float(np.percentile(durs, 10)) if durs else None,
            "p90": float(np.percentile(durs, 90)) if durs else None,
            "max": float(np.max(durs)) if durs else None,
        },
        "text_chars": {
            "mean": float(text_lens.mean()),
            "p90": float(text_lens.quantile(0.9)),
            "over_250": int((text_lens > 250).sum()),
        },
        "suspect_wavs": bad_files[:50],
        "suspect_wavs_total": len(bad_files),
        "notes": [
            "Rows with text_chars > 250 often truncate in XTTS tokenizer warnings.",
            "Near-zero RMS clips should be removed or re-cut; they hurt training.",
            "MFCC cosine vs ref is a rough speaker-likeness hint, not perceptual quality.",
        ],
    }

    if args.ref_wav and args.synth_wav:
        ref_p = args.ref_wav.expanduser().resolve()
        syn_p = args.synth_wav.expanduser().resolve()
        if not ref_p.is_file() or not syn_p.is_file():
            print("ref-wav or synth-wav not found", file=sys.stderr)
            return 1
        sr = 24000
        y_ref, _ = load_mono(str(ref_p), sr)
        y_syn, _ = load_mono(str(syn_p), sr)
        # Use comparable length: mean embedding on full ref vs full synth (weak for long mismatch).
        e_ref = _mfcc_mean_embedding(y_ref, sr)
        e_syn = _mfcc_mean_embedding(y_syn, sr)
        sim = cosine_sim(e_ref, e_syn)
        report["ref_vs_synth"] = {
            "ref": str(ref_p),
            "synth": str(syn_p),
            "mfcc_cosine_similarity_trim_first_3s": sim,
            "ref_duration_s": float(len(y_ref) / sr),
            "synth_duration_s": float(len(y_syn) / sr),
            "mfcc_note": "Coarse timbre hint only; can sit high for any clean speech. Use listening A/B and dataset fixes first.",
        }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(json.dumps(report, indent=2))
        print(
            "\nHow to improve (typical order of impact):\n"
            "  1) Drop or fix suspect_wavs; re-run --train-only on cloud.\n"
            "  2) Rebuild dataset with a larger Whisper model for cleaner boundaries/text.\n"
            "  3) More clean source audio (minutes, varied prosody) > raw epoch count.\n"
            "  4) Tune inference: gpt_cond_len / temperature / use 2–4 good ref clips.\n",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
