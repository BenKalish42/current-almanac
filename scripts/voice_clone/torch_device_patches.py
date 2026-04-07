"""
Patch Coqui's `trainer` package so XTTS GPT fine-tuning runs on Apple MPS when CUDA
is unavailable. CUDA training uses Coqui defaults (unchanged). Safe to call once per process.
"""
from __future__ import annotations

import os
from typing import Optional

import torch

_PATCHED = False
_ORIG_TRAINER_INIT = None
_ORIG_GET_AUTOCAST = None
_TRAIN_DEVICE: Optional[torch.device] = None


def training_torch_device() -> torch.device:
    if os.environ.get("XTTS_TRAIN_CPU", "").strip().lower() in ("1", "true", "yes"):
        return torch.device("cpu")
    if torch.cuda.is_available():
        return torch.device("cuda:0")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def apply_mps_trainer_patches() -> str:
    """Return device string used for training (cuda:0, mps, or cpu)."""
    global _PATCHED, _ORIG_TRAINER_INIT, _ORIG_GET_AUTOCAST, _TRAIN_DEVICE

    dev = training_torch_device()
    _TRAIN_DEVICE = dev
    if _PATCHED:
        return str(dev)

    import trainer.generic_utils as gu
    import trainer.trainer as tr_mod

    if dev.type != "mps":
        _PATCHED = True
        return str(dev)

    def to_mps(x):
        if x is None:
            return None
        if torch.is_tensor(x):
            return x.contiguous().to(dev, non_blocking=True)
        return x

    gu.to_cuda = to_mps
    # `trainer.trainer` binds `to_cuda` at import time; fixing only generic_utils leaves batches on CPU.
    tr_mod.to_cuda = to_mps

    _ORIG_TRAINER_INIT = tr_mod.Trainer.__init__

    def _init_move_model_to_mps(self, *args, **kwargs):
        _ORIG_TRAINER_INIT(self, *args, **kwargs)
        if not torch.cuda.is_available():
            self.model.to(dev)
            if isinstance(self.criterion, list):
                for c in self.criterion:
                    if isinstance(c, torch.nn.Module):
                        c.to(dev)
            elif isinstance(self.criterion, torch.nn.Module):
                self.criterion.to(dev)

    tr_mod.Trainer.__init__ = _init_move_model_to_mps

    _ORIG_GET_AUTOCAST = tr_mod.Trainer._get_autocast_args

    def _get_autocast_args_patched(self, *, mixed_precision: bool, precision: str):
        if mixed_precision:
            d = torch.float32
            if precision == "fp16":
                d = torch.float16
            elif precision == "bf16":
                d = torch.bfloat16
            return "mps", d
        return _ORIG_GET_AUTOCAST(self, mixed_precision=mixed_precision, precision=precision)

    tr_mod.Trainer._get_autocast_args = _get_autocast_args_patched  # type: ignore[assignment]

    _PATCHED = True
    print(f"> Patched Coqui Trainer for Apple MPS ({dev}).", flush=True)
    return str(dev)
