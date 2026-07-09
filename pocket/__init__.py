"""Pocket detection module."""
from __future__ import annotations
import logging
from workflow.contracts import PipelineContext, PocketResult, Pocket
from pocket.fpocket import run_fpocket

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Detect binding pockets from prepared protein structure."""
    struct = ctx.previous["structure"]
    pocket_cfg = ctx.config.get("pocket", {})
    top_n = pocket_cfg.get("top_pockets", 3)

    pockets = run_fpocket(struct.pdb_path, top_n=top_n)
    if not pockets:
        logger.warning(f"[{ctx.job_id}] No pockets found, using default box")
        pockets = [
            Pocket(rank=1, center=(0.0, 0.0, 0.0), size=(25.0, 25.0, 25.0),
                   druggability_score=0.5, volume=500.0)
        ]

    result = PocketResult(pockets=pockets)

    new_previous = dict(ctx.previous)
    new_previous["pocket"] = result
    return PipelineContext(
        job_id=ctx.job_id,
        gene_symbol=ctx.gene_symbol,
        disease=ctx.disease,
        config=ctx.config,
        previous=new_previous,
    )
