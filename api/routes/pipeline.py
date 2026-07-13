"""Full pipeline endpoint."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from api.schemas import PipelineRequest

router = APIRouter()


@router.post("/run")
async def run_pipeline(request: PipelineRequest):
    """Run the full Target-to-Hit pipeline."""
    import uuid
    from workflow.contracts import PipelineContext
    from workflow.config import load_config
    from workflow.engine import WorkflowEngine

    from target_assessment import run as target_assessment_run
    from structure import run as structure_run
    from pocket import run as pocket_run
    from screening import run as screening_run
    from docking import run as docking_run
    from ranking import run as ranking_run
    from annotation import run as annotation_run
    from report import run as report_run

    job_id = str(uuid.uuid4())[:8]
    config = load_config()
    if request.config_overrides:
        from workflow.config import _deep_merge
        _deep_merge(config, request.config_overrides)

    ctx = PipelineContext(
        job_id=job_id,
        gene_symbol=request.gene_symbol,
        disease=request.disease,
        config=config,
    )

    engine = WorkflowEngine(preserve_partial=True)
    engine.register("target_assessment", target_assessment_run)
    engine.register("structure", structure_run)
    engine.register("pocket", pocket_run)
    engine.register("screening", screening_run)
    engine.register("docking", docking_run)
    engine.register("ranking", ranking_run)
    engine.register("annotation", annotation_run)
    engine.register("report", report_run)

    try:
        ctx = engine.run(ctx)
        hits = ctx.previous.get("ranking")
        return {
            "job_id": job_id,
            "status": "completed",
            "gene_symbol": request.gene_symbol,
            "num_hits": len(hits.hits) if hits else 0,
            "top_hit": {
                "id": hits.hits[0].compound_id,
                "score": hits.hits[0].final_score,
            } if hits and hits.hits else None,
            "report_path": str(ctx.previous.get("report", {}).report_json or ""),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
