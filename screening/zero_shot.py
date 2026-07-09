"""Zero-shot virtual screening via cosine similarity."""
from __future__ import annotations
import logging
import time
import numpy as np
from typing import List
from screening.protein_encoder import ProteinEncoder
from screening.ligand_encoder import LigandEncoder
from screening.compound_library import CompoundLibrary
from workflow.contracts import ScreeningResult, ScoredCompound, ScreeningConfig

logger = logging.getLogger(__name__)


def run_zero_shot_screening(
    protein_sequence: str,
    library: CompoundLibrary,
    config: ScreeningConfig,
) -> ScreeningResult:
    """Run zero-shot screening: encode protein, encode ligands, cosine rank."""
    t0 = time.monotonic()

    protein_encoder = ProteinEncoder(config.protein_model, device=config.device)
    protein_emb = protein_encoder.encode(protein_sequence)
    logger.info(f"Protein embedding shape: {protein_emb.shape}")

    ligand_encoder = LigandEncoder(config.ligand_model, device=config.device)
    all_smiles = [c.smiles for c in library.compounds]
    ligand_embs = ligand_encoder.encode_batch(all_smiles, batch_size=config.batch_size)
    logger.info(f"Ligand embeddings shape: {ligand_embs.shape}")

    # Optional projection to shared space
    if config.projection_dim > 0:
        protein_emb = _project(protein_emb, protein_emb.shape[0], config.projection_dim)
        ligand_embs = _project_batch(ligand_embs, ligand_embs.shape[1], config.projection_dim)

    # Cosine similarity
    protein_norm = protein_emb / (np.linalg.norm(protein_emb) + 1e-8)
    ligand_norms = ligand_embs / (np.linalg.norm(ligand_embs, axis=1, keepdims=True) + 1e-8)
    similarities = np.dot(ligand_norms, protein_norm)

    # Rank and return top N
    ranked: List[ScoredCompound] = []
    indices = np.argsort(similarities)[::-1][:config.top_n]
    for idx in indices:
        c = library.compounds[idx]
        ranked.append(ScoredCompound(
            compound_id=c.compound_id,
            smiles=c.smiles,
            ai_score=float(similarities[idx]),
        ))

    elapsed = time.monotonic() - t0
    logger.info(f"Screening completed in {elapsed:.1f}s, top score: {ranked[0].ai_score:.4f}")
    return ScreeningResult(
        ranked_compounds=ranked,
        protein_embedding=protein_emb,
        elapsed_seconds=elapsed,
    )


def _project(emb: np.ndarray, in_dim: int, out_dim: int) -> np.ndarray:
    rng = np.random.RandomState(42)
    proj = rng.randn(in_dim, out_dim) / np.sqrt(in_dim)
    return emb @ proj


def _project_batch(emb: np.ndarray, in_dim: int, out_dim: int) -> np.ndarray:
    rng = np.random.RandomState(42)
    proj = rng.randn(in_dim, out_dim) / np.sqrt(in_dim)
    return emb @ proj
