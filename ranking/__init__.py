"""Consensus Ranking module."""
from __future__ import annotations
import logging
from workflow.contracts import PipelineContext, RankingResult
from ranking.scorer import consensus_score

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Compute consensus ranking from screening and docking results."""
    screening = ctx.previous["screening"]
    docking = ctx.previous["docking"]
    weights = ctx.config.get("ranking", {}).get("weights", {})

    hits = consensus_score(screening.ranked_compounds, docking.poses, weights)

    logger.info(f"[{ctx.job_id}] Ranked {len(hits)} hits, top: {hits[0].compound_id} score={hits[0].final_score:.3f}")

    result = RankingResult(hits=hits)

    new_previous = dict(ctx.previous)
    new_previous["ranking"] = result
    return PipelineContext(
        job_id=ctx.job_id, gene_symbol=ctx.gene_symbol,
        disease=ctx.disease, config=ctx.config, previous=new_previous,
    )
