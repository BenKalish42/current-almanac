#!/usr/bin/env bash
# Build a tarball: training scripts + existing xtts_ft_output/dataset (no re-Whisper on cloud).
# Streams into tar (no full duplicate of wavs on disk).
# Run:  bash scripts/voice_clone/cloud/package_for_cloud.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VC_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
# Set OUT_TAR=/path/on/larger/disk/bundle.tar.gz if the repo volume is low on space.
OUT_TAR="${OUT_TAR:-${SCRIPT_DIR}/xtts_cloud_training_bundle.tar.gz}"
DATASET="${VC_DIR}/xtts_ft_output/dataset"

if [[ ! -f "${DATASET}/metadata_train.csv" || ! -f "${DATASET}/metadata_eval.csv" ]]; then
  echo "ERROR: Missing dataset under ${DATASET}" >&2
  echo "Expected metadata_train.csv and metadata_eval.csv (your completed Step 1)." >&2
  exit 1
fi

mkdir -p "$(dirname "${OUT_TAR}")"
tar -czf "${OUT_TAR}" \
  -C "${VC_DIR}" \
    train_xtts_full.py \
    gpt_train_local.py \
    torch_device_patches.py \
    xtts_ft_output/dataset \
  -C "${SCRIPT_DIR}" \
    requirements-cloud-gpu.txt \
    setup_ubuntu_gpu.sh \
    train_gpu.sh

echo "Wrote ${OUT_TAR}"
du -h "${OUT_TAR}"
