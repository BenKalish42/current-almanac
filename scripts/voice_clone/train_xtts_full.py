#!/usr/bin/env python3
"""
Full XTTS v2 fine-tuning pipeline (same stages as Coqui's Gradio demo, without UI):

  1) Transcribe audio, slice into sentence-aligned clips, write metadata CSVs.
     - Apple Silicon / MPS or CPU: OpenAI Whisper (PyTorch) uses the GPU via MPS.
     - NVIDIA: default uses faster-whisper on CUDA (CTranslate2); optional --asr-backend torch
  2) Fine-tune the XTTS GPT encoder. On Mac without CUDA, trainer patches route tensors
     and the model to MPS (see torch_device_patches.py).

Before running:
  export COQUI_TOS_AGREED=1   # https://coqui.ai/cpml
  # Recommended on Mac:
  export PYTORCH_ENABLE_MPS_FALLBACK=1

Usage:
  source scripts/voice_clone/.venv-voice/bin/activate
  export COQUI_TOS_AGREED=1
  python3 scripts/voice_clone/train_xtts_full.py /path/to/TomTraining.mp3 \\
      --out scripts/voice_clone/xtts_ft_output --epochs 10
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import shutil
import sys
from pathlib import Path

# Coqui TOS required for downloads inside train_gpt
if os.environ.get("COQUI_TOS_AGREED") != "1":
    print(
        "Set COQUI_TOS_AGREED=1 after reading https://coqui.ai/cpml",
        file=sys.stderr,
    )
    sys.exit(1)

_VOICE_CLONE_DIR = str(Path(__file__).resolve().parent)
if _VOICE_CLONE_DIR not in sys.path:
    sys.path.insert(0, _VOICE_CLONE_DIR)

import pandas as pd
import torch
import torchaudio
from tqdm import tqdm

from TTS.tts.layers.xtts.tokenizer import multilingual_cleaners


def _pick_asr_backend(explicit: str) -> str:
    if explicit != "auto":
        return explicit
    if torch.cuda.is_available():
        return "faster"
    return "torch"


def _whisper_torch_device_str() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _word_triple(word) -> tuple[str, float, float]:
    if isinstance(word, dict):
        return (
            word.get("word") or "",
            float(word.get("start", 0)),
            float(word.get("end", 0)),
        )
    return (
        getattr(word, "word", None) or "",
        float(getattr(word, "start", 0)),
        float(getattr(word, "end", 0)),
    )


def _append_clips_from_words(
    words_list: list,
    *,
    wav: torch.Tensor,
    sr: int,
    audio_path: str,
    out_path: str,
    buffer: float,
    speaker_name: str,
    target_language: str,
    metadata: dict,
) -> None:
    i_ref = metadata["_i"]
    audio_file_name, _ = os.path.splitext(os.path.basename(audio_path))

    if not words_list:
        return

    sentence = ""
    sentence_start = None
    first_word = True

    for word_idx, word in enumerate(words_list):
        wtext, w_start, w_end = _word_triple(word)
        if not wtext:
            continue

        if first_word:
            sentence_start = w_start
            if word_idx == 0:
                sentence_start = max(sentence_start - buffer, 0)
            else:
                _, _, previous_word_end = _word_triple(words_list[word_idx - 1])
                sentence_start = max(sentence_start - buffer, (previous_word_end + sentence_start) / 2)
            sentence = wtext
            first_word = False
        else:
            sentence += wtext

        if wtext[-1] not in [".", "!", "?"]:
            continue

        sentence = sentence[1:] if len(sentence) > 1 else sentence
        sentence = multilingual_cleaners(sentence, target_language)
        clip_idx = i_ref[0]
        audio_file = f"wavs/{audio_file_name}_{str(clip_idx).zfill(8)}.wav"

        if word_idx + 1 < len(words_list):
            next_word_start = _word_triple(words_list[word_idx + 1])[1]
        else:
            next_word_start = (wav.shape[0] - 1) / sr

        word_end = min((w_end + next_word_start) / 2, w_end + buffer)
        absolute_path = os.path.join(out_path, audio_file)
        os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
        i_ref[0] = clip_idx + 1
        first_word = True

        audio = wav[int(sr * sentence_start) : int(sr * word_end)].unsqueeze(0)
        if audio.size(-1) < sr / 3:
            continue
        torchaudio.save(absolute_path, audio, sr)

        metadata["audio_file"].append(audio_file)
        metadata["text"].append(sentence)
        metadata["speaker_name"].append(speaker_name)


def format_audio_list(
    audio_files: list[str],
    *,
    target_language: str = "en",
    out_path: str,
    buffer: float = 0.2,
    eval_percentage: float = 0.15,
    speaker_name: str = "speaker",
    whisper_model: str = "large-v2",
    asr_backend: str = "auto",
) -> tuple[str, str, float]:
    """Align-clips + transcription → Coqui XTTS fine-tune CSVs."""
    os.makedirs(out_path, exist_ok=True)
    backend = _pick_asr_backend(asr_backend)
    metadata = {"audio_file": [], "text": [], "speaker_name": [], "_i": [0]}
    audio_total_size = 0.0

    if backend == "faster":
        from faster_whisper import WhisperModel

        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"
        print(f"Loading faster-whisper ({whisper_model}) on {device} ({compute_type})…", flush=True)
        asr_model = WhisperModel(whisper_model, device=device, compute_type=compute_type)

        for audio_path in tqdm(audio_files, desc="Formatting audio (faster-whisper)"):
            wav, sr = torchaudio.load(audio_path)
            if wav.size(0) != 1:
                wav = torch.mean(wav, dim=0, keepdim=True)
            wav = wav.squeeze()
            audio_total_size += wav.size(-1) / sr

            segments, _ = asr_model.transcribe(audio_path, word_timestamps=True, language=target_language)
            words_list = []
            for segment in segments:
                words_list.extend(segment.words or [])
            _append_clips_from_words(
                words_list,
                wav=wav,
                sr=sr,
                audio_path=audio_path,
                out_path=out_path,
                buffer=buffer,
                speaker_name=speaker_name,
                target_language=target_language,
                metadata=metadata,
            )

        del asr_model
        gc.collect()

    else:
        import whisper

        dev_str = _whisper_torch_device_str()
        use_fp16 = dev_str != "cpu"
        print(
            f"Loading OpenAI Whisper ({whisper_model}) on {dev_str} (fp16={use_fp16})…",
            flush=True,
        )
        try:
            model = whisper.load_model(whisper_model, device=dev_str)
        except (NotImplementedError, RuntimeError) as exc:
            if dev_str == "mps":
                reason = str(exc).strip().split("\n")[0][:240]
                print(
                    f"Whisper could not load on MPS ({type(exc).__name__}); using CPU for ASR. {reason}",
                    flush=True,
                )
                dev_str = "cpu"
                use_fp16 = False
                model = whisper.load_model(whisper_model, device="cpu")
            else:
                raise

        for audio_path in tqdm(audio_files, desc="Formatting audio (whisper+torch)"):
            wav, sr = torchaudio.load(audio_path)
            if wav.size(0) != 1:
                wav = torch.mean(wav, dim=0, keepdim=True)
            wav = wav.squeeze()
            audio_total_size += wav.size(-1) / sr

            try:
                result = model.transcribe(
                    audio_path,
                    word_timestamps=True,
                    language=target_language,
                    verbose=False,
                    fp16=use_fp16,
                )
            except RuntimeError:
                if use_fp16 and dev_str == "mps":
                    print("Whisper fp16 failed on MPS; retrying in fp32…", flush=True)
                    result = model.transcribe(
                        audio_path,
                        word_timestamps=True,
                        language=target_language,
                        verbose=False,
                        fp16=False,
                    )
                else:
                    raise
            words_list = []
            for seg in result.get("segments") or []:
                for w in seg.get("words") or []:
                    words_list.append(
                        {
                            "word": w.get("word", "") or "",
                            "start": float(w["start"]),
                            "end": float(w["end"]),
                        }
                    )
            _append_clips_from_words(
                words_list,
                wav=wav,
                sr=sr,
                audio_path=audio_path,
                out_path=out_path,
                buffer=buffer,
                speaker_name=speaker_name,
                target_language=target_language,
                metadata=metadata,
            )

        del model
        gc.collect()

    del metadata["_i"]

    if not metadata["audio_file"]:
        raise RuntimeError(
            "No aligned clips were produced. Check language (--lang), audio quality, or try --whisper-model small."
        )

    df = pd.DataFrame(metadata)
    df = df.sample(frac=1, random_state=42)
    n_val = int(len(df) * eval_percentage)
    n_val = max(1, n_val)
    if n_val >= len(df):
        n_val = max(1, len(df) // 5)
    if n_val >= len(df):
        n_val = len(df) - 1
    df_eval = df[:n_val]
    df_train = df[n_val:]
    if len(df_train) < 1:
        raise RuntimeError("Not enough clips for a training split after validation holdout; add more audio.")
    df_train = df_train.sort_values("audio_file")
    df_eval = df_eval.sort_values("audio_file")

    train_csv = os.path.join(out_path, "metadata_train.csv")
    eval_csv = os.path.join(out_path, "metadata_eval.csv")
    df_train.to_csv(train_csv, sep="|", index=False)
    df_eval.to_csv(eval_csv, sep="|", index=False)

    return train_csv, eval_csv, audio_total_size


def main() -> int:
    p = argparse.ArgumentParser(description="XTTS v2 full fine-tune (dataset + GPT encoder)")
    p.add_argument(
        "audio",
        nargs="*",
        type=Path,
        default=[],
        help="Training audio file(s): wav, mp3, flac (omit with --train-only)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).resolve().parent / "xtts_ft_output",
        help="Base output dir (dataset/ + run/training/ created inside)",
    )
    p.add_argument("--lang", default="en", help="Language code for Whisper + trainer")
    p.add_argument("--speaker-name", default="tom", help="Speaker column in metadata")
    p.add_argument("--whisper-model", default="large-v2", help="e.g. tiny, small, medium, large-v2")
    p.add_argument(
        "--asr-backend",
        choices=("auto", "torch", "faster"),
        default="auto",
        help="auto: faster-whisper on CUDA, else OpenAI Whisper (MPS/CPU/CUDA)",
    )
    p.add_argument("--epochs", type=int, default=10)
    p.add_argument("--batch-size", type=int, default=2, help="Lower if GPU OOM")
    p.add_argument("--grad-acumm", type=int, default=2)
    p.add_argument(
        "--max-audio-sec",
        type=float,
        default=11.0,
        help="Max clip length in seconds (passed to trainer as 22050*s)",
    )
    p.add_argument(
        "--dataset-only",
        action="store_true",
        help="Only build dataset (Whisper + clips); do not train",
    )
    p.add_argument(
        "--train-only",
        action="store_true",
        help="Skip ASR/dataset build; use existing --out/dataset metadata CSVs and wavs",
    )
    args = p.parse_args()

    if args.dataset_only and args.train_only:
        print("ERROR: use only one of --dataset-only or --train-only", file=sys.stderr)
        return 1

    base_out = args.out.expanduser().resolve()
    base_out.mkdir(parents=True, exist_ok=True)
    dataset_dir = base_out / "dataset"

    if args.train_only:
        train_csv = str(dataset_dir / "metadata_train.csv")
        eval_csv = str(dataset_dir / "metadata_eval.csv")
        if not os.path.isfile(train_csv) or not os.path.isfile(eval_csv):
            print(
                f"ERROR: --train-only requires {train_csv} and {eval_csv}",
                file=sys.stderr,
            )
            return 1
        audio_total = 999999.0
    else:
        audio_paths = [str(a.expanduser().resolve()) for a in args.audio]
        if not audio_paths:
            print("ERROR: pass at least one audio file, or use --train-only", file=sys.stderr)
            return 1
        for ap in audio_paths:
            if not os.path.isfile(ap):
                print(f"ERROR: not a file: {ap}", file=sys.stderr)
                return 1

        train_csv, eval_csv, audio_total = format_audio_list(
            audio_paths,
            target_language=args.lang,
            out_path=str(dataset_dir),
            speaker_name=args.speaker_name,
            whisper_model=args.whisper_model,
            asr_backend=args.asr_backend,
        )

    if audio_total < 120:
        print(
            "ERROR: Coqui recommends at least ~2 minutes of source audio total.",
            file=sys.stderr,
        )
        return 1

    n_train = len(pd.read_csv(train_csv, sep="|"))
    n_eval = len(pd.read_csv(eval_csv, sep="|"))
    if n_train < 2:
        print("ERROR: Too few training clips after processing.", file=sys.stderr)
        return 1

    print(f"Dataset: {n_train} train / {n_eval} eval rows under {dataset_dir}", file=sys.stderr)

    if args.dataset_only:
        print(f"train_csv={train_csv}\neval_csv={eval_csv}")
        return 0

    from gpt_train_local import train_gpt

    max_audio_length = int(args.max_audio_sec * 22050)
    config_path, _orig_ckpt, vocab_file, exp_path, speaker_ref = train_gpt(
        args.lang,
        args.epochs,
        args.batch_size,
        args.grad_acumm,
        train_csv,
        eval_csv,
        output_path=str(base_out),
        max_audio_length=max_audio_length,
    )

    shutil.copy2(config_path, exp_path)
    shutil.copy2(vocab_file, exp_path)

    ref_path = Path(speaker_ref)
    if not ref_path.is_file():
        ref_path = (base_out / "dataset" / speaker_ref).resolve()
    speaker_ref_abs = str(ref_path) if ref_path.is_file() else str(speaker_ref)

    exp_s = os.fspath(exp_path)
    info = {
        "fine_tuned_checkpoint": os.path.join(exp_s, "best_model.pth"),
        "trainer_output": exp_s,
        "original_xtts_config_copied_to": str(Path(exp_s) / Path(config_path).name),
        "vocab_copied_to": str(Path(exp_s) / Path(vocab_file).name),
        "speaker_reference_wav": speaker_ref_abs,
    }
    info_path = base_out / "fine_tune_paths.json"
    info_path.write_text(json.dumps(info, indent=2), encoding="utf-8")

    print("\nFine-tune finished.\n" + json.dumps(info, indent=2))
    print(f"\nPaths saved to {info_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
