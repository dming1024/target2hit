"""Tests for workflow contracts."""
import numpy as np
from pathlib import Path
from workflow.contracts import (
    PipelineContext,
    StructureResult,
    Pocket,
    PocketResult,
    ScreeningConfig,
    ScoredCompound,
    ScreeningResult,
    DockedPose,
    DockingResult,
    RankedHit,
    RankingResult,
    AnnotationResult,
    ReportResult,
)


class TestPipelineContext:
    def test_create_context(self):
        ctx = PipelineContext(
            job_id="test-001",
            gene_symbol="EGFR",
            disease="NSCLC",
            config={"mode": "test"},
        )
        assert ctx.job_id == "test-001"
        assert ctx.gene_symbol == "EGFR"
        assert ctx.disease == "NSCLC"
        assert ctx.previous == {}

    def test_context_is_frozen(self):
        ctx = PipelineContext(
            job_id="test-001",
            gene_symbol="EGFR",
            disease=None,
            config={},
        )
        try:
            ctx.job_id = "hacked"
            assert False, "Should have raised FrozenInstanceError"
        except Exception:
            pass


class TestScreeningContracts:
    def test_scored_compound(self):
        c = ScoredCompound(
            compound_id="CHEMBL123",
            smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
            ai_score=0.85,
        )
        assert c.compound_id == "CHEMBL123"
        assert c.smiles == "CC(=O)OC1=CC=CC=C1C(=O)O"
        assert c.ai_score == 0.85
        assert c.embedding is None

    def test_screening_config_defaults(self):
        cfg = ScreeningConfig()
        assert cfg.mode == "zero_shot"
        assert cfg.protein_model == "esm2_t30_150M_UR50D"
        assert cfg.mlp_weights is None
        assert cfg.top_n == 500


class TestDockingContracts:
    def test_docked_pose(self):
        pose = DockedPose(
            compound_id="CHEMBL123",
            binding_energy=-8.5,
            pose_file=Path("/tmp/pose.pdbqt"),
        )
        assert pose.binding_energy == -8.5


class TestPipelineContextIntegration:
    def test_previous_accumulates_module_outputs(self):
        ctx = PipelineContext(
            job_id="test-001", gene_symbol="EGFR", disease=None, config={}
        )
        # Simulate structure module output
        struct = StructureResult(
            pdb_path=Path("/tmp/egfr.pdb"),
            protein_sequence="MPSK...",
            source="pdb",
            resolution=2.1,
            uniprot_id="P00533",
        )
        ctx = PipelineContext(
            job_id=ctx.job_id,
            gene_symbol=ctx.gene_symbol,
            disease=ctx.disease,
            config=ctx.config,
            previous={"structure": struct},
        )
        retrieved = ctx.previous["structure"]
        assert isinstance(retrieved, StructureResult)
        assert retrieved.protein_sequence == "MPSK..."
