"""Target Assessment module adapter.

Wraps the existing target_assessment pipeline to conform to
the PipelineModule protocol: def run(ctx) -> ctx.
"""
from __future__ import annotations
import logging
from workflow.contracts import PipelineContext

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Run target assessment using the existing engine.

    Reads: ctx.gene_symbol, ctx.disease
    Writes: ctx.previous["target_assessment"] = dict with assessment result
    """
    from target_assessment.assessment_core import run_assessment

    disease = ctx.disease or "pan-cancer"
    result = run_assessment(
        gene=ctx.gene_symbol,
        disease=disease,
        scenario=ctx.config.get("scenario", "general"),
    )

    logger.info(
        f"[{ctx.job_id}] Target assessment: {ctx.gene_symbol} "
        f"score={result.get('total_score', 'N/A')} "
        f"grade={result.get('grade', 'N/A')}"
    )

    new_previous = dict(ctx.previous)
    new_previous["target_assessment"] = result
    return PipelineContext(
        job_id=ctx.job_id,
        gene_symbol=ctx.gene_symbol,
        disease=ctx.disease,
        config=ctx.config,
        previous=new_previous,
    )
