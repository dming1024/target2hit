"""Consensus scoring: weighted integration of AI, docking, and molecular properties."""
from __future__ import annotations
from typing import List, Dict
import numpy as np
from workflow.contracts import ScoredCompound, DockedPose, RankedHit
from ranking.filters import compute_drug_likeness, check_pains, compute_sa_score, compute_novelty


def consensus_score(
    screening_results: List[ScoredCompound],
    docking_results: List[DockedPose],
    weights: Dict[str, float],
) -> List[RankedHit]:
    """Compute consensus ranking from AI screening and docking results."""
    dock_map = {p.compound_id: p.binding_energy for p in docking_results}

    # Normalize AI scores to [0, 1]
    ai_scores = np.array([c.ai_score for c in screening_results])
    ai_min, ai_max = ai_scores.min(), ai_scores.max()
    ai_range = ai_max - ai_min if ai_max > ai_min else 1.0
    ai_norm = (ai_scores - ai_min) / ai_range

    # Normalize docking scores
    dock_scores = np.array([dock_map.get(c.compound_id, 0.0) for c in screening_results])
    dock_min, dock_max = dock_scores.min(), dock_scores.max()
    dock_range = dock_max - dock_min if dock_max > dock_min else 1.0
    dock_norm = 1.0 - (dock_scores - dock_min) / dock_range

    hits = []
    for i, c in enumerate(screening_results):
        qed = compute_drug_likeness(c.smiles)
        pains = 1.0 if check_pains(c.smiles) else 0.0
        sa = min(compute_sa_score(c.smiles) / 10.0, 1.0)
        novelty = compute_novelty(c.smiles)

        final = (
            weights.get("ai_score", 0.30) * ai_norm[i]
            + weights.get("dock_score", 0.30) * dock_norm[i]
            + weights.get("drug_likeness", 0.15) * qed
            + weights.get("novelty", 0.10) * novelty
            - weights.get("sa_penalty", 0.10) * sa
            - weights.get("pains_penalty", 0.05) * pains
        )

        hits.append(RankedHit(
            rank=0, compound_id=c.compound_id, smiles=c.smiles,
            final_score=float(final), ai_score=c.ai_score,
            dock_score=dock_scores[i], drug_likeness=qed,
            sa_score=sa, pains_flag=bool(pains), novelty=novelty,
        ))

    hits.sort(key=lambda h: h.final_score, reverse=True)
    for rank, hit in enumerate(hits, start=1):
        object.__setattr__(hit, "rank", rank)

    return hits
