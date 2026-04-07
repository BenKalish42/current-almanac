#!/usr/bin/env python3
"""
Synthesize one line with a GPT-fine-tuned XTTS checkpoint (best_model.pth + config + vocab).

  export COQUI_TOS_AGREED=1
  source .venv-voice/bin/activate
  python scripts/voice_clone/xtts_synthesize_finetune.py \\
    --checkpoint-dir .../GPT_XTTS_FT-.../ \\
    --speaker-wav path/to/ref.wav \\
    --text "Hello." \\
    --out out.wav
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import torch
import torchaudio

if os.environ.get("COQUI_TOS_AGREED") != "1":
    print("Set COQUI_TOS_AGREED=1 (https://coqui.ai/cpml)", file=sys.stderr)
    raise SystemExit(1)

from TTS.config import load_config
from TTS.tts.models.xtts import Xtts


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint-dir", type=Path, required=True, help="Folder with config.json, vocab.json, best_model.pth")
    p.add_argument("--speaker-wav", type=Path, required=True, action="append", dest="speaker_wavs", help="Reference WAV (repeatable)")
    p.add_argument("--text", type=str, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--language", default="en")
    p.add_argument("--gpt-cond-len", type=int, default=12)
    args = p.parse_args()

    ck_dir = args.checkpoint_dir.expanduser().resolve()
    cfg_path = ck_dir / "config.json"
    vocab_path = ck_dir / "vocab.json"
    ck_path = ck_dir / "best_model.pth"
    for path in (cfg_path, vocab_path, ck_path):
        if not path.is_file():
            print(f"Missing: {path}", file=sys.stderr)
            return 1

    speaker_wav = [str(p.expanduser().resolve()) for p in args.speaker_wavs]

    config = load_config(str(cfg_path))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_path=str(ck_path), vocab_path=str(vocab_path), eval=True)
    device = "cuda" if torch.cuda.is_available() else "mps" if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available() else "cpu"
    model = model.to(device)

    config.gpt_cond_len = args.gpt_cond_len
    out = model.synthesize(args.text, config, speaker_wav, args.language)
    wav = torch.tensor(out["wav"]).unsqueeze(0)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(args.out), wav.cpu(), 24000)
    print(f"Wrote {args.out} ({wav.shape[-1] / 24000:.1f}s @ 24kHz)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
