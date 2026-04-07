#!/usr/bin/env python3
"""
Synthesize with **stock** XTTS v2 (no GPT fine-tune checkpoint).

This matches the path used in `xtts_conversation.py` and the original “smoketest”:
reference wav(s) → voice conditioning only; decoder stays Coqui-pretrained.

  export COQUI_TOS_AGREED=1
  source .venv-voice/bin/activate
  python scripts/voice_clone/xtts_synthesize_pretrained.py \\
    --text "Hello." \\
    --out outputs/xtts_smoke_pretrained.wav

By default uses all `reference_clips/*.wav` if any exist, else `xtts_lambda_model/speaker_ref.wav`.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if os.environ.get("COQUI_TOS_AGREED") != "1":
    print("Set COQUI_TOS_AGREED=1 (https://coqui.ai/cpml)", file=sys.stderr)
    raise SystemExit(1)


def pick_device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_speaker_wavs(
    script_dir: Path,
    clips_dir: Path | None,
    speaker_wavs: list[Path],
) -> list[Path]:
    if clips_dir is not None:
        d = clips_dir.expanduser().resolve()
        wavs = sorted(d.glob("*.wav"))
        if not wavs:
            print(f"No .wav files in {d}", file=sys.stderr)
            raise SystemExit(1)
        return wavs
    if speaker_wavs:
        out = [p.expanduser().resolve() for p in speaker_wavs]
        for p in out:
            if not p.is_file():
                print(f"Missing: {p}", file=sys.stderr)
                raise SystemExit(1)
        return out
    ref_clips = script_dir / "reference_clips"
    fallback = sorted(ref_clips.glob("*.wav"))
    if fallback:
        return fallback
    single = script_dir / "xtts_lambda_model" / "speaker_ref.wav"
    if not single.is_file():
        print(
            "No reference audio: add clips under reference_clips/, or pass --speaker-wav / --clips-dir.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return [single]


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description="XTTS v2 stock (pretrained) + reference clone")
    p.add_argument("--text", type=str, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--clips-dir", type=Path, default=None, help="Use all *.wav in this folder")
    p.add_argument(
        "--speaker-wav",
        type=Path,
        action="append",
        dest="speaker_wavs",
        default=[],
        help="Reference WAV (repeatable). Ignored if --clips-dir is set.",
    )
    p.add_argument("--language", default="en")
    args = p.parse_args()

    wavs = resolve_speaker_wavs(script_dir, args.clips_dir, args.speaker_wavs)
    paths = [str(w) for w in wavs]

    from TTS.api import TTS

    device = pick_device()
    if device == "mps":
        print("Using MPS. If errors occur: export PYTORCH_ENABLE_MPS_FALLBACK=1", file=sys.stderr)

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    out = args.out.expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Do not pass `speaker=` unless that voice is already in Coqui's cache (see xtts_conversation warmup).
    tts.tts_to_file(
        text=args.text,
        file_path=str(out),
        speaker_wav=paths if len(paths) > 1 else paths[0],
        language=args.language,
    )
    print(f"Wrote {out} (stock XTTS v2, {len(paths)} ref clip(s))", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
