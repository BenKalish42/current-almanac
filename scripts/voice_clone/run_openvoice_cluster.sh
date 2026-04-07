#!/usr/bin/env bash
# Bootstrap OpenVoice v2 on a Linux GPU instance, then synthesize the benchmark line.
#
# On the cluster (after scp of TomTraining.mp3):
#   chmod +x run_openvoice_cluster.sh
#   REFERENCE_AUDIO=~/TomTraining.mp3 OUT_WAV=~/benchmark.wav ./run_openvoice_cluster.sh
#
# Or positional:
#   ./run_openvoice_cluster.sh ~/TomTraining.mp3 ~/benchmark.wav
#
# Optional: OPENVOICE_WORKSPACE=/data/openvoice-ws  CUDA_WHEEL=cu121

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="${OPENVOICE_WORKSPACE:-$SCRIPT_DIR/.openvoice-workspace}"
REPO_DIR="$WORKSPACE/OpenVoice"
VENV="$WORKSPACE/venv"
CKPT_ZIP_URL="https://myshell-public-repo-host.s3.amazonaws.com/openvoice/checkpoints_v2_0417.zip"
CKPT_FLAG="$WORKSPACE/.checkpoints_v2_ok"

REFERENCE_AUDIO="${REFERENCE_AUDIO:-${1:-}}"
OUT_WAV="${OUT_WAV:-${2:-}}"
if [[ -z "${REFERENCE_AUDIO}" || -z "${OUT_WAV}" ]]; then
  echo "Usage: REFERENCE_AUDIO=path/to/audio.mp3 OUT_WAV=path/out.wav $0" >&2
  echo "   or: $0 path/to/audio.mp3 path/out.wav" >&2
  exit 1
fi

mkdir -p "$WORKSPACE"

if [[ ! -d "$VENV" ]]; then
  PY=python3
  if command -v python3.10 &>/dev/null; then PY=python3.10; fi
  "$PY" -m venv "$VENV"
fi
# shellcheck source=/dev/null
source "$VENV/bin/activate"
python -m pip install -U pip wheel

TORCH_INDEX=""
if command -v nvidia-smi &>/dev/null; then
  WHEEL="${CUDA_WHEEL:-cu121}"
  TORCH_INDEX="https://download.pytorch.org/whl/${WHEEL}"
  echo "Detected NVIDIA GPU; installing torch from ${TORCH_INDEX}" >&2
  pip install torch torchvision torchaudio --index-url "$TORCH_INDEX"
else
  pip install torch torchvision torchaudio
fi

if [[ ! -d "$REPO_DIR/.git" ]]; then
  mkdir -p "$(dirname "$REPO_DIR")"
  git clone --depth 1 https://github.com/myshell-ai/OpenVoice.git "$REPO_DIR"
fi
pip install -e "$REPO_DIR"
pip install -r "$REPO_DIR/requirements.txt"
pip install "git+https://github.com/myshell-ai/MeloTTS.git"
python -m unidic download

if [[ ! -f "$CKPT_FLAG" ]]; then
  echo "Downloading OpenVoice v2 checkpoints (large)…" >&2
  mkdir -p "$WORKSPACE/dl"
  curl -L -o "$WORKSPACE/dl/checkpoints_v2_0417.zip" "$CKPT_ZIP_URL"
  unzip -q -o "$WORKSPACE/dl/checkpoints_v2_0417.zip" -d "$REPO_DIR"
  touch "$CKPT_FLAG"
fi

exec python "$SCRIPT_DIR/openvoice_benchmark.py" \
  --openvoice-home "$REPO_DIR" \
  --reference "$REFERENCE_AUDIO" \
  --out "$OUT_WAV"
