"""Job status and report retrieval."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

# In-memory job store (V1; replace with DB in V2)
_jobs: dict = {}


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and partial results."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@router.get("/{job_id}/report")
async def get_report(job_id: str, format: str = "json"):
    """Download report file."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    report_path = job.get("report_path")
    if not report_path or not Path(report_path).exists():
        raise HTTPException(status_code=404, detail="Report not yet generated")

    return FileResponse(report_path, media_type="application/json",
                        filename=f"report_{job_id}.json")
