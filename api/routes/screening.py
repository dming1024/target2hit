"""Screening-only endpoint."""
from __future__ import annotations
from fastapi import APIRouter
from api.schemas import ScreeningRequest
from workflow.contracts import PipelineContext, StructureResult
import uuid
from pathlib import Path

router = APIRouter()


@router.post("/run")
async def run_screening(request: ScreeningRequest):
    """Run AI screening as a standalone step."""
    from screening import run as screening_run
    from structure import run as structure_run

    job_id = str(uuid.uuid4())[:8]

    if request.protein_sequence:
        # Skip structure module
        structure_result = StructureResult(
            pdb_path=Path("/dev/null"),
            protein_sequence=request.protein_sequence,
            source="manual",
            uniprot_id="",
        )
        ctx = PipelineContext(
            job_id=job_id,
            gene_symbol=request.gene_symbol,
            disease=request.disease,
            config={"screening": {"mode": request.mode, "top_n": request.top_n}},
            previous={"structure": structure_result},
        )
    else:
        # Run structure module first
        ctx = PipelineContext(
            job_id=job_id,
            gene_symbol=request.gene_symbol,
            disease=request.disease,
            config={},
        )
        ctx = structure_run(ctx)
        ctx = PipelineContext(
            job_id=ctx.job_id,
            gene_symbol=ctx.gene_symbol,
            disease=ctx.disease,
            config={"screening": {"mode": request.mode, "top_n": request.top_n}},
            previous=ctx.previous,
        )

    ctx = screening_run(ctx)
    result = ctx.previous["screening"]

    return {
        "job_id": job_id,
        "status": "completed",
        "num_compounds_screened": len(result.ranked_compounds),
        "top_compounds": [
            {"id": c.compound_id, "smiles": c.smiles, "score": c.ai_score}
            for c in result.ranked_compounds[:10]
        ],
        "elapsed_seconds": result.elapsed_seconds,
    }
