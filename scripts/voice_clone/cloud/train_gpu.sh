#!/usr/bin/env bash
# Run GPT fine-tune only (dataset already under ./xtts_ft_output/dataset).
# Usage (after setup_ubuntu_gpu.sh):  source .venv-xtts/bin/activate && export COQUI_TOS_AGREED=1 && bash train_gpu.sh
set -euo pipefail

cd "$(dirname "$0")"

if [[ "${COQUI_TOS_AGREED:-}" != "1" ]]; then
  echo "ERROR: export COQUI_TOS_AGREED=1  (see https://coqui.ai/cpml)" >&2
  exit 1
fi

if [[ ! -f xtts_ft_output/dataset/metadata_train.csv ]]; then
  echo "ERROR: unpack xtts_cloud_training_bundle.tar.gz here first (need xtts_ft_output/dataset)." >&2
  exit 1
fi

# Unset Mac-only CPU override if present
unset XTTS_TRAIN_CPU
# Linux: multiprocessing loaders sometimes hang with Coqui; 0 is slower but reliable.
export XTTS_DATALOADER_WORKERS="${XTTS_DATALOADER_WORKERS:-0}"

# Raise --batch-size on large GPUs; lower to 4 or 2 if you hit CUDA OOM.
python train_xtts_full.py \
  --out xtts_ft_output \
  --train-only \
  --epochs 20 \
  --batch-size 8 \
  --grad-acumm 1 \
  --speaker-name tom

echo "Done. Check xtts_ft_output/fine_tune_paths.json and run/training/*/best_model*.pth"
