"""End-to-end pipeline integration test."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from workflow.contracts import PipelineContext, Pocket
from workflow.engine import WorkflowEngine
from workflow.config import load_config


@pytest.mark.integration
class TestPipelineEndToEnd:
    @patch("structure.clean_pdb")
    @patch("docking.prepare_receptor")
    @patch("docking.prepare_ligand")
    @patch("docking.dock_parallel")
    @patch("screening.zero_shot.ProteinEncoder")
    @patch("screening.zero_shot.LigandEncoder")
    @patch("pocket.run_fpocket")
    @patch("structure.download_structure")
    @patch("structure.search_pdb")
    @patch("structure.resolve_uniprot")
    @patch("target_assessment.run")
    def test_full_pipeline(
        self,
        mock_ta,
        mock_resolve,
        mock_search,
        mock_download,
        mock_fpocket,
        mock_lig_enc,
        mock_prot_enc,
        mock_parallel,
        mock_ligand_prep,
        mock_prepare_receptor,
        mock_clean_pdb,
    ):
        """Run full pipeline with mocked external dependencies."""
        import numpy as np
        from workflow.contracts import (
            StructureResult, Pocket, PocketResult,
            ScreeningResult, ScoredCompound,
            DockingResult, DockedPose,
        )

        # Mock target assessment
        mock_ta.return_value = PipelineContext(
            job_id="e2e-001", gene_symbol="EGFR", disease="NSCLC", config={},
            previous={"target_assessment": {"total_score": 82.5, "grade": "A"}},
        )

        # Mock structure
        mock_resolve.return_value = "P00533"
        mock_search.return_value = {"pdb_id": "1M17", "resolution": 2.1, "source": "pdb"}
        mock_download.return_value = (Path("/tmp/1m17.pdb"), "pdb")
        mock_clean_pdb.return_value = (Path("/tmp/1m17_clean.pdb"), "MQLFHLPSRL")

        # Mock pocket
        mock_fpocket.return_value = [
            Pocket(rank=1, center=(10, 20, 30), size=(20, 20, 20),
                   druggability_score=0.85, volume=450)
        ]

        # Mock screening
        mock_prot = mock_prot_enc.return_value
        mock_prot.encode.return_value = np.ones(640)
        mock_lig = mock_lig_enc.return_value
        mock_lig.encode_batch.return_value = np.random.randn(10, 600)

        # Mock docking
        mock_ligand_prep.return_value = Path("/tmp/lig.pdbqt")
        mock_prepare_receptor.return_value = Path("/tmp/receptor.pdbqt")
        mock_parallel.return_value = [
            DockedPose(f"C00{i}", -8.0 - i * 0.5, Path(f"/tmp/pose{i}.pdbqt"))
            for i in range(1, 6)
        ]

        # Build context and run
        config = load_config()
        config["screening"]["device"] = "cpu"
        config["compound_library"] = {"max_compounds": 10}

        ctx = PipelineContext(
            job_id="e2e-001", gene_symbol="EGFR", disease="NSCLC", config=config,
        )

        import target_assessment, structure, pocket, screening, docking, ranking, annotation, report

        engine = WorkflowEngine(preserve_partial=True)
        engine.register("target_assessment", target_assessment)
        engine.register("structure", structure)
        engine.register("pocket", pocket)
        engine.register("screening", screening)
        engine.register("docking", docking)
        engine.register("ranking", ranking)
        engine.register("annotation", annotation)
        engine.register("report", report)

        result = engine.run(ctx)

        # Verify all steps produced output
        assert "target_assessment" in result.previous
        assert "structure" in result.previous
        assert "pocket" in result.previous
        assert "screening" in result.previous
        assert "docking" in result.previous
        assert "ranking" in result.previous
        assert "annotation" in result.previous
        assert "report" in result.previous

        # Verify ranking has correct output
        ranking = result.previous["ranking"]
        assert len(ranking.hits) > 0
        assert ranking.hits[0].rank == 1

        # Verify report files exist
        report = result.previous["report"]
        assert report.report_json.exists()
