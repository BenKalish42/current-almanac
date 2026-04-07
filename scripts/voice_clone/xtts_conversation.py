#!/usr/bin/env python3
"""
Interactive dialogue: you type a line, an LLM replies, XTTS v2 speaks the reply
in a voice cloned from reference WAV clips.

Prerequisites:
  1) pip install -r scripts/voice_clone/requirements.txt  (preferably in a venv)
  2) python scripts/voice_clone/prepare_reference_clips.py [path/to/training.mp3]
  3) DEEPSEEK_API_KEY or OPENAI_API_KEY in backend/.env (same pattern as backend)
  4) export COQUI_TOS_AGREED=1 after reading CPML (https://coqui.ai/cpml) — required
     for XTTS download/use; without it, Coqui prompts interactively and scripts fail.

First synthesis call caches the cloned speaker under `speaker_id` (see Coqui docs).

Note: This script uses reference-based cloning. For many clips from a long
recording, see prepare_reference_clips.py. For full GPT-encoder fine-tuning
(Whisper labels + training), see train_xtts_full.py. GPU or Apple MPS speeds
inference; CPU works but is slow.

Ethical use: only clone voices you have permission to use.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from openai import OpenAI


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def load_backend_env() -> None:
    env_path = project_root() / "backend" / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                os.environ.setdefault(key.strip(), val)


def get_llm_client() -> tuple[OpenAI, str]:
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    if deepseek_key:
        api_key = deepseek_key
        base_url = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        model = os.environ.get("VOICE_CHAT_MODEL", "deepseek-chat")
    elif openai_key:
        api_key = openai_key
        base_url = os.environ.get("VOICE_CHAT_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("VOICE_CHAT_MODEL", "gpt-4o-mini")
    else:
        raise SystemExit(
            "Set DEEPSEEK_API_KEY or OPENAI_API_KEY (e.g. in backend/.env)."
        )
    return OpenAI(api_key=api_key, base_url=base_url), model


def chat_reply(client: OpenAI, model: str, user_text: str, history: list[dict]) -> str:
    system = """You are the user's dialogue partner in a voice conversation they are listening to.
Respond in plain text only (no markdown). Keep replies to one or two short sentences unless they ask for detail.
Match the user's tone; be natural and direct."""

    messages = [{"role": "system", "content": system}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        max_tokens=500,
        temperature=0.7,
    )
    text = (resp.choices[0].message.content or "").strip()
    return text


def pick_device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def play_wav(path: Path) -> None:
    if sys.platform == "darwin":
        subprocess.run(["afplay", str(path)], check=False)
    else:
        print(f"(Install player or open manually): {path}", file=sys.stderr)


def main() -> int:
    load_backend_env()

    parser = argparse.ArgumentParser(description="LLM + XTTS voice dialogue")
    parser.add_argument(
        "--clips-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "reference_clips",
        help="Directory with reference .wav files",
    )
    parser.add_argument(
        "--speaker-id",
        default="TomTraining",
        help="Cached voice id in Coqui voices folder",
    )
    parser.add_argument(
        "--language",
        default="en",
        help="XTTS language code (e.g. en)",
    )
    parser.add_argument("--no-play", action="store_true", help="Do not afplay output")
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write replies here (default: tempfile dir)",
    )
    args = parser.parse_args()

    clips_dir = args.clips_dir.expanduser().resolve()
    wavs = sorted(clips_dir.glob("*.wav"))
    if not wavs:
        print(
            f"No WAV clips in {clips_dir}. Run:\n"
            f"  python3 scripts/voice_clone/prepare_reference_clips.py path/to/training.mp3\n",
            file=sys.stderr,
        )
        return 1

    try:
        client, model = get_llm_client()
    except SystemExit as e:
        print(str(e), file=sys.stderr)
        return 1

    if os.environ.get("COQUI_TOS_AGREED") != "1":
        print(
            "Coqui XTTS requires license acceptance (CPML or commercial).\n"
            "Read https://coqui.ai/cpml then run: export COQUI_TOS_AGREED=1",
            file=sys.stderr,
        )
        return 1

    print("Loading XTTS (first run downloads weights; this can take a while)...", file=sys.stderr)
    import torch
    from TTS.api import TTS

    device = pick_device()
    if device == "mps":
        print("Using Apple MPS. If you hit errors, set PYTORCH_ENABLE_MPS_FALLBACK=1.", file=sys.stderr)

    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)

    out_dir = args.out_dir
    if out_dir is None:
        out_dir = Path(tempfile.mkdtemp(prefix="xtts_dialog_"))
    else:
        out_dir = out_dir.expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    history: list[dict] = []

    print(
        f"Ready. Reference clips: {len(wavs)} | Speaker cache: {args.speaker_id} | LLM: {model}\n"
        "Type your line (empty line to quit).\n",
        file=sys.stderr,
    )

    # Prime cache once with full reference list
    warmup_path = out_dir / "_warmup.wav"
    try:
        tts.tts_to_file(
            text="Warm-up line for voice caching.",
            file_path=str(warmup_path),
            speaker_wav=[str(p) for p in wavs],
            speaker=args.speaker_id,
            language=args.language,
        )
        warmup_path.unlink(missing_ok=True)
    except Exception as e:
        print(f"Warm-up / cache failed: {e}", file=sys.stderr)
        return 1

    while True:
        try:
            line = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.", file=sys.stderr)
            break
        if not line:
            break

        reply = chat_reply(client, model, line, history)
        if not reply:
            print("(empty LLM reply)", file=sys.stderr)
            continue

        history.append({"role": "user", "content": line})
        history.append({"role": "assistant", "content": reply})

        # Trim history for token limits
        if len(history) > 20:
            history = history[-20:]

        out_wav = out_dir / f"reply_{uuid.uuid4().hex[:8]}.wav"
        print(f"Assistant: {reply}\nSynthesizing → {out_wav}", file=sys.stderr)
        try:
            tts.tts_to_file(
                text=reply,
                file_path=str(out_wav),
                speaker=args.speaker_id,
                language=args.language,
            )
        except Exception as e:
            print(f"TTS failed: {e}", file=sys.stderr)
            continue

        if not args.no_play:
            play_wav(out_wav)

    return 0


if __name__ == "__main__":
    sys.exit(main())
