"""Compound annotation module."""
from __future__ import annotations
import logging
from typing import Dict
from workflow.contracts import PipelineContext, AnnotationResult
import annotation.fetcher

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Annotate top hit compounds with external database metadata."""
    hits = ctx.previous["ranking"].hits[:50]
    annotations: Dict[str, Dict[str, str]] = {}

    for hit in hits:
        anno: Dict[str, str] = {}
        anno.update(annotation.fetcher.fetch_pubchem(hit.smiles))
        anno.update(annotation.fetcher.fetch_chembl(hit.smiles))
        annotations[hit.compound_id] = anno

    logger.info(f"[{ctx.job_id}] Annotated {len(annotations)} compounds")

    result = AnnotationResult(annotations=annotations)

    new_previous = dict(ctx.previous)
    new_previous["annotation"] = result
    return PipelineContext(
        job_id=ctx.job_id, gene_symbol=ctx.gene_symbol,
        disease=ctx.disease, config=ctx.config, previous=new_previous,
    )
