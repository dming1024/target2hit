"""Protein sequence encoder using ESM2."""
from __future__ import annotations
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ESM2_CONFIGS = {
    "esm2_t30_150M_UR50D": {"dim": 640, "layers": 30},
    "esm2_t33_650M_UR50D": {"dim": 1280, "layers": 33},
    "esm2_t36_3B_UR50D": {"dim": 2560, "layers": 36},
}


class ProteinEncoder:
    """Encode protein sequences with ESM2 via HuggingFace transformers."""

    def __init__(self, model_name: str = "esm2_t30_150M_UR50D", device: str = "auto"):
        self.model_name = model_name
        self.device = self._resolve_device(device)
        self.embedding_dim = ESM2_CONFIGS[model_name]["dim"]
        self._model: Optional[object] = None
        self._tokenizer: Optional[object] = None

    def _resolve_device(self, device: str) -> str:
        if device == "auto":
            try:
                import torch
                return "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                return "cpu"
        return device

    def _load_model(self):
        if self._model is None:
            from transformers import EsmModel, EsmTokenizer
            self._tokenizer = EsmTokenizer.from_pretrained(f"facebook/{self.model_name}")
            self._model = EsmModel.from_pretrained(f"facebook/{self.model_name}").to(self.device)
            self._model.eval()
            logger.info(f"Loaded {self.model_name} on {self.device}")

    def encode(self, sequence: str):
        """Encode a single protein sequence. Returns (embedding_dim,) array."""
        import torch
        import numpy as np
        self._load_model()
        encoded = self._tokenizer(sequence, return_tensors="pt")
        encoded = {k: v.to(self.device) for k, v in encoded.items()}

        with torch.no_grad():
            outputs = self._model(**encoded)
            embeddings = outputs.last_hidden_state[:, 1:-1, :].mean(dim=1)

        return embeddings.squeeze(0).cpu().numpy()
