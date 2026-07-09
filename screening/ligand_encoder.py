"""Ligand SMILES encoder using ChemBERTa."""
from __future__ import annotations
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class LigandEncoder:
    """Encode SMILES strings with ChemBERTa via HuggingFace transformers."""

    def __init__(self, model_name: str = "ChemBERTa-77M-MLM", device: str = "auto"):
        self.model_name = model_name
        self.device = self._resolve_device(device)
        self.embedding_dim = 600
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
            from transformers import AutoModel, AutoTokenizer
            try:
                model_id = f"DeepChem/{self.model_name}"
                self._tokenizer = AutoTokenizer.from_pretrained(model_id)
                self._model = AutoModel.from_pretrained(model_id).to(self.device)
            except Exception:
                logger.warning(f"Failed to load {self.model_name}, falling back")
                model_id = "seyonec/PubChem10M_SMILES_BPE_450k"
                self._tokenizer = AutoTokenizer.from_pretrained(model_id)
                self._model = AutoModel.from_pretrained(model_id).to(self.device)
            self._model.eval()
            logger.info(f"Loaded ligand encoder on {self.device}")

    def encode(self, smiles: str):
        """Encode a single SMILES. Returns (embedding_dim,) array."""
        import torch
        import numpy as np
        self._load_model()
        encoded = self._tokenizer(smiles, return_tensors="pt", padding=True, truncation=True, max_length=512)
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        with torch.no_grad():
            outputs = self._model(**encoded)
            embedding = outputs.last_hidden_state[:, 0, :]
        return embedding.squeeze(0).cpu().numpy()

    def encode_batch(self, smiles_list: List[str], batch_size: int = 256):
        """Encode a batch of SMILES. Returns (N, embedding_dim)."""
        import torch
        import numpy as np
        all_embeddings = []
        for i in range(0, len(smiles_list), batch_size):
            batch = smiles_list[i:i + batch_size]
            self._load_model()
            encoded = self._tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
            encoded = {k: v.to(self.device) for k, v in encoded.items()}
            with torch.no_grad():
                outputs = self._model(**encoded)
                embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
            all_embeddings.append(embeddings)
        return np.concatenate(all_embeddings, axis=0)
