"""MLP fusion head for affinity prediction (V2, not implemented in V1)."""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import numpy as np
from workflow.contracts import ScreeningResult, ScreeningConfig


class MLPPredictor:
    """MLP-based protein-ligand affinity predictor. NOT IMPLEMENTED in V1."""

    def __init__(self, weights_path: Optional[Path] = None):
        if weights_path is None:
            raise NotImplementedError(
                "MLP mode requires trained weights. "
                "Train on BindingDB/PDBBind data first, then pass weights_path. "
                "Use mode='zero_shot' for V1."
            )

    def predict(self, protein_emb: np.ndarray, ligand_embs: np.ndarray) -> np.ndarray:
        raise NotImplementedError("MLP prediction not available in V1")
