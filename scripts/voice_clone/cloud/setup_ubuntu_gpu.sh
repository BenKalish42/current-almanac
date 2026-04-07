#!/usr/bin/env bash
# Ubuntu 22.04+ with NVIDIA driver already working (nvidia-smi OK).
# Usage:  bash setup_ubuntu_gpu.sh
set -euo pipefail

if ! command -v nvidia-smi &>/dev/null; then
  echo "ERROR: nvidia-smi not found. Install NVIDIA driver / CUDA image on the GPU VM first." >&2
  exit 1
fi

nvidia-smi

sudo apt-get update -qq
sudo apt-get install -y python3 python3-venv python3-pip

cd "$(dirname "$0")"
python3 -m venv .venv-xtts
# shellcheck source=/dev/null
source .venv-xtts/bin/activate
pip install -U pip wheel

# PyTorch with CUDA 12.4 wheels (matches many cloud L4/A10/A100 images).
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements-cloud-gpu.txt
# Coqui imports break on transformers 5.x (missing isin_mps_friendly); 4.57.x matches coqui-tts>=0.27.
pip install "transformers==4.57.3"

python -c "import torch; print('torch', torch.__version__, 'cuda?', torch.cuda.is_available())"

echo "OK. Next: export COQUI_TOS_AGREED=1 && source .venv-xtts/bin/activate && bash train_gpu.sh"
