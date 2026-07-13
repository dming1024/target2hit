"""Pydantic request/response schemas."""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class PipelineRequest(BaseModel):
    gene_symbol: str = Field(..., min_length=1, max_length=32, examples=["EGFR"])
    disease: Optional[str] = Field(None, examples=["NSCLC"])
    config_overrides: Dict = Field(default_factory=dict)


class ScreeningRequest(BaseModel):
    gene_symbol: str = Field(..., min_length=1, max_length=32)
    disease: Optional[str] = None
    protein_sequence: Optional[str] = None  # override structure module
    mode: str = "zero_shot"
    top_n: int = Field(500, ge=1, le=10000)


class DockingRequest(BaseModel):
    job_id: Optional[str] = None  # reuse screening results from existing job
    compounds: Optional[List[Dict]] = None  # or provide compounds directly
    protein_pdb_path: Optional[str] = None
    pocket_center: Optional[List[float]] = None
    pocket_size: Optional[List[float]] = None


class JobStatus(BaseModel):
    job_id: str
    gene_symbol: str
    disease: Optional[str]
    status: str
    current_module: Optional[str]
    error_message: Optional[str]
    result_summary: Optional[Dict]
