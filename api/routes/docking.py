"""Docking-only endpoint."""
from __future__ import annotations
from fastapi import APIRouter
from api.schemas import DockingRequest
from workflow.contracts import (
    PipelineContext, StructureResult, PocketResult, Pocket,
    ScreeningResult, ScoredCompound,
)
import uuid
from pathlib import Path

router = APIRouter()


@router.post("/run")
async def run_docking(request: DockingRequest):
    """Run molecular docking as a standalone step."""
    from docking import run as docking_run

    job_id = request.job_id or str(uuid.uuid4())[:8]

    if request.compounds:
        compounds = [
            ScoredCompound(
                compound_id=c.get("id", f"LIG_{i}"),
                smiles=c["smiles"],
                ai_score=c.get("score", 0.5),
            )
            for i, c in enumerate(request.compounds)
        ]
    else:
        # Sample compound for testing
        compounds = [
            ScoredCompound("TEST001", "CC(=O)OC1=CC=CC=C1C(=O)O", 0.9)
        ]

    center = request.pocket_center or [0.0, 0.0, 0.0]
    psize = request.pocket_size or [25.0, 25.0, 25.0]

    ctx = PipelineContext(
        job_id=job_id,
        gene_symbol="manual",
        disease=None,
        config={"docking": {"exhaustiveness": 8, "num_cpus": 4, "box_padding": 4.0}},
        previous={
            "structure": StructureResult(
                pdb_path=Path(request.protein_pdb_path or "/dev/null"),
                protein_sequence="",
                source="manual",
            ),
            "pocket": PocketResult(pockets=[
                Pocket(rank=1, center=tuple(center), size=tuple(psize),
                       druggability_score=0.8, volume=500)
            ]),
            "screening": ScreeningResult(ranked_compounds=compounds),
        },
    )

    ctx = docking_run(ctx)
    result = ctx.previous["docking"]

    return {
        "job_id": job_id,
        "status": "completed",
        "num_docked": len(result.poses),
        "top_poses": [
            {"id": p.compound_id, "binding_energy": p.binding_energy}
            for p in sorted(result.poses, key=lambda x: x.binding_energy)[:10]
        ],
        "elapsed_seconds": result.elapsed_seconds,
    }
