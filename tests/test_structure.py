"""Tests for structure preparation module."""
from pathlib import Path
from unittest.mock import patch
from workflow.contracts import PipelineContext, StructureResult
from structure import run


@patch("structure.resolve_uniprot")
@patch("structure.search_pdb")
@patch("structure.download_structure")
@patch("structure.clean_pdb")
def test_structure_pipeline(mock_clean, mock_download, mock_search, mock_resolve):
    mock_resolve.return_value = "P00533"
    mock_search.return_value = {"pdb_id": "1M17", "resolution": 2.1, "source": "pdb"}
    mock_download.return_value = (Path("/tmp/1M17.pdb"), "pdb")
    mock_clean.return_value = (Path("/tmp/1M17_clean.pdb"), "MPSK...SEQUENCE")

    ctx = PipelineContext(
        job_id="test-001",
        gene_symbol="EGFR",
        disease="NSCLC",
        config={"structure": {"prefer_experimental": True, "max_resolution": 3.0}},
    )
    result = run(ctx)

    sr = result.previous["structure"]
    assert isinstance(sr, StructureResult)
    assert sr.protein_sequence == "MPSK...SEQUENCE"
    assert sr.source == "pdb"
    assert sr.resolution == 2.1
    assert sr.uniprot_id == "P00533"
    mock_resolve.assert_called_once_with("EGFR")
    mock_search.assert_called_once()
    mock_download.assert_called_once()
    mock_clean.assert_called_once()
