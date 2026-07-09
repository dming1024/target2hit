"""Tests for pocket detection module."""
from pathlib import Path
from unittest.mock import patch
from workflow.contracts import PipelineContext, StructureResult, PocketResult, Pocket
from pocket import run


@patch("pocket.run_fpocket")
def test_pocket_detection(mock_fpocket):
    mock_fpocket.return_value = [
        Pocket(
            rank=1,
            center=(10.0, 20.0, 30.0),
            size=(20.0, 20.0, 20.0),
            druggability_score=0.85,
            volume=450.0,
        ),
        Pocket(
            rank=2,
            center=(5.0, 15.0, 25.0),
            size=(15.0, 15.0, 15.0),
            druggability_score=0.55,
            volume=200.0,
        ),
    ]

    ctx = PipelineContext(
        job_id="test-001",
        gene_symbol="EGFR",
        disease=None,
        config={"pocket": {"algorithm": "fpocket", "top_pockets": 3}},
        previous={
            "structure": StructureResult(
                pdb_path=Path("/tmp/egfr_clean.pdb"),
                protein_sequence="MPSK",
                source="pdb",
                resolution=2.1,
                uniprot_id="P00533",
            )
        },
    )
    result = run(ctx)
    pr = result.previous["pocket"]
    assert isinstance(pr, PocketResult)
    assert len(pr.pockets) == 2
    assert pr.pockets[0].rank == 1
    assert pr.pockets[0].druggability_score == 0.85
    mock_fpocket.assert_called_once()
