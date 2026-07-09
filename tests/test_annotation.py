"""Tests for annotation module."""
from unittest.mock import patch
from workflow.contracts import PipelineContext, RankingResult, RankedHit, AnnotationResult
from annotation import run


@patch("annotation.fetcher.fetch_pubchem")
@patch("annotation.fetcher.fetch_chembl")
def test_annotation(mock_chembl, mock_pubchem):
    mock_pubchem.return_value = {"pubchem_cid": "2244"}
    mock_chembl.return_value = {"chembl_id": "CHEMBL25", "max_phase": "4"}

    ctx = PipelineContext(
        job_id="test-001", gene_symbol="EGFR", disease=None, config={},
        previous={"ranking": RankingResult(hits=[
            RankedHit(rank=1, compound_id="C001", smiles="CC(=O)O",
                      final_score=0.9, ai_score=0.9, dock_score=-8.5,
                      drug_likeness=0.8, sa_score=0.1, pains_flag=False),
        ])},
    )
    result = run(ctx)
    ar = result.previous["annotation"]
    assert isinstance(ar, AnnotationResult)
    assert ar.annotations["C001"]["pubchem_cid"] == "2244"
