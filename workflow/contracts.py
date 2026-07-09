"""Pipeline contracts: all module I/O dataclasses.

All dataclasses are frozen (immutable). Modules communicate only through
PipelineContext.previous dict, keyed by module name.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Tuple
import numpy as np


# ---------------------------------------------------------------------------
# Pipeline Context
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineContext:
    """Flows through all modules. Each module reads from .previous and
    returns a new PipelineContext with its output added."""
    job_id: str
    gene_symbol: str
    disease: Optional[str]
    config: Dict[str, Any]
    previous: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Screening
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScreeningConfig:
    mode: Literal["zero_shot", "mlp"] = "zero_shot"
    protein_model: str = "esm2_t30_150M_UR50D"
    ligand_model: str = "ChemBERTa-77M-MLM"
    mlp_weights: Optional[Path] = None
    projection_dim: int = 256
    batch_size: int = 256
    top_n: int = 500
    device: str = "auto"


@dataclass(frozen=True)
class ScoredCompound:
    compound_id: str
    smiles: str
    ai_score: float
    embedding: Optional[np.ndarray] = None


@dataclass(frozen=True)
class ScreeningResult:
    ranked_compounds: List[ScoredCompound]
    protein_embedding: Optional[np.ndarray] = None
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StructureResult:
    pdb_path: Path
    protein_sequence: str
    source: Literal["pdb", "alphafold"]
    resolution: Optional[float] = None
    uniprot_id: str = ""


# ---------------------------------------------------------------------------
# Pocket
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Pocket:
    rank: int
    center: Tuple[float, float, float]
    size: Tuple[float, float, float]
    druggability_score: float
    volume: float


@dataclass(frozen=True)
class PocketResult:
    pockets: List[Pocket]


# ---------------------------------------------------------------------------
# Docking
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DockedPose:
    compound_id: str
    binding_energy: float  # kcal/mol
    pose_file: Path        # PDBQT output


@dataclass(frozen=True)
class DockingResult:
    poses: List[DockedPose]
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Ranking
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RankedHit:
    rank: int
    compound_id: str
    smiles: str
    final_score: float
    ai_score: float
    dock_score: float
    drug_likeness: float
    sa_score: float
    pains_flag: bool
    novelty: float = 0.0


@dataclass(frozen=True)
class RankingResult:
    hits: List[RankedHit]


# ---------------------------------------------------------------------------
# Annotation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AnnotationResult:
    annotations: Dict[str, Dict[str, str]]
    # compound_id -> {source: value, ...}


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReportResult:
    report_json: Path
    report_html: Optional[Path] = None
    report_pdf: Optional[Path] = None
