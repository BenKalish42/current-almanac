#!/usr/bin/env python3
"""
OpenVoice v2 + MeloTTS: clone tone from a reference recording (MP3/WAV), synthesize text.

Designed to run on a GPU box after OpenVoice is installed (see run_openvoice_cluster.sh).

Example:
  source .openvoice-workspace/venv/bin/activate
  python openvoice_benchmark.py \\
    --openvoice-home /path/to/OpenVoice \\
    --reference /path/to/TomTraining.mp3 \\
    --out outputs/benchmark.wav
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

DEFAULT_TEXT = (
    "It's over you capitalist pig, now give your son the money he rightfully deserves "
    "for putting up with a liar."
)


def main() -> int:
    p = argparse.ArgumentParser(description="OpenVoice v2 benchmark synth (MeloTTS base + tone convert)")
    p.add_argument(
        "--openvoice-home",
        type=Path,
        required=True,
        help="Path to cloned OpenVoice repo (contains checkpoints_v2/)",
    )
    p.add_argument("--reference", type=Path, required=True, help="Reference MP3/WAV to clone")
    p.add_argument("--out", type=Path, required=True, help="Output WAV path")
    p.add_argument("--text", type=str, default=DEFAULT_TEXT)
    p.add_argument(
        "--language",
        default="EN_NEWEST",
        help="MeloTTS language tag (e.g. EN_NEWEST, EN)",
    )
    p.add_argument(
        "--device",
        default=None,
        help="Force torch device (e.g. cuda:0, cpu). Default: cuda:0 if available else cpu",
    )
    p.add_argument(
        "--melo-speed",
        type=float,
        default=1.0,
        help="MeloTTS speed factor",
    )
    args = p.parse_args()

    repo = args.openvoice_home.expanduser().resolve()
    ref = args.reference.expanduser().resolve()
    out = args.out.expanduser().resolve()

    ckpt_root = repo / "checkpoints_v2"
    conv_dir = ckpt_root / "converter"
    for path in (conv_dir / "config.json", conv_dir / "checkpoint.pth"):
        if not path.is_file():
            print(f"Missing OpenVoice checkpoint file: {path}", file=sys.stderr)
            return 1
    if not ref.is_file():
        print(f"Missing reference audio: {ref}", file=sys.stderr)
        return 1

    if args.device:
        device = args.device
    elif __import__("torch").cuda.is_available():
        device = "cuda:0"
    else:
        device = "cpu"

    import torch
    from melo.api import TTS
    from openvoice import se_extractor
    from openvoice.api import ToneColorConverter

    out.parent.mkdir(parents=True, exist_ok=True)

    tone_color_converter = ToneColorConverter(str(conv_dir / "config.json"), device=device)
    tone_color_converter.load_ckpt(str(conv_dir / "checkpoint.pth"))

    target_se, _audio_tag = se_extractor.get_se(str(ref), tone_color_converter, vad=True)
    if isinstance(target_se, torch.Tensor):
        target_se = target_se.to(device)

    model = TTS(language=args.language, device=device)
    speaker_ids = model.hps.data.spk2id
    speaker_key = next(iter(speaker_ids.keys()))
    speaker_id = speaker_ids[speaker_key]
    sk_file = speaker_key.lower().replace("_", "-")
    ses_path = ckpt_root / "base_speakers" / "ses" / f"{sk_file}.pth"
    if not ses_path.is_file():
        print(f"Missing base speaker embedding: {ses_path}", file=sys.stderr)
        return 1
    source_se = torch.load(str(ses_path), map_location=device)

    with tempfile.TemporaryDirectory(prefix="openvoice_melo_") as tmp:
        src_wav = Path(tmp) / "melo_base.wav"
        model.tts_to_file(args.text, speaker_id, str(src_wav), speed=args.melo_speed)
        tone_color_converter.convert(
            audio_src_path=str(src_wav),
            src_se=source_se,
            tgt_se=target_se,
            output_path=str(out),
            message="@MyShell",
        )

    print(f"Wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
