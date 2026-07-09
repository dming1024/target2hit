"""Tests for AI screening module."""
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
import numpy as np
from workflow.contracts import PipelineContext, ScreeningResult, StructureResult
from screening import run


@patch("screening.zero_shot.ProteinEncoder")
@patch("screening.zero_shot.LigandEncoder")
def test_zero_shot_screening_entry_point(mock_ligand_enc, mock_protein_enc):
    mock_protein = mock_protein_enc.return_value
    mock_protein.encode.return_value = np.ones(640)

    mock_ligand = mock_ligand_enc.return_value
    mock_ligand.encode_batch.return_value = np.array([
        [1.0] * 600, [0.5] * 600, [0.1] * 600
    ])

    ctx = PipelineContext(
        job_id="test-001",
        gene_symbol="EGFR",
        disease=None,
        config={
            "screening": {
                "mode": "zero_shot",
                "top_n": 500,
                "batch_size": 256,
                "device": "cpu",
            },
            "compound_library": {"max_compounds": 100000},
        },
        previous={
            "structure": StructureResult(
                pdb_path=Path("/tmp/test.pdb"),
                protein_sequence="MPSK",
                source="pdb",
                uniprot_id="P00533",
            )
        },
    )
    result = run(ctx)
    sr = result.previous["screening"]
    assert isinstance(sr, ScreeningResult)
    assert len(sr.ranked_compounds) == 3
    assert sr.ranked_compounds[0].compound_id in ("SAMPLE001", "C001")


def test_mlp_mode_raises_not_implemented():
    ctx = PipelineContext(
        job_id="test-001",
        gene_symbol="EGFR",
        disease=None,
        config={"screening": {"mode": "mlp"}},
        previous={
            "structure": StructureResult(
                pdb_path=Path("/tmp/test.pdb"),
                protein_sequence="MPSK",
                source="pdb",
                uniprot_id="P00533",
            )
        },
    )
    try:
        run(ctx)
        assert False, "Should have raised NotImplementedError"
    except NotImplementedError:
        pass
