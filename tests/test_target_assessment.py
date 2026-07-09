"""Tests for target assessment integration."""
from unittest.mock import patch, MagicMock
from workflow.contracts import PipelineContext
from target_assessment import run


@patch("target_assessment.assessment_core.run_assessment")
def test_target_assessment_adapter(mock_run_assessment):
    mock_run_assessment.return_value = {
        "gene": "EGFR",
        "disease": "NSCLC",
        "total_score": 82.5,
        "grade": "A",
        "recommendation": "Strong target",
        "scores": {"disease_relevance": 12, "expression": 10},
    }

    ctx = PipelineContext(
        job_id="test-001",
        gene_symbol="EGFR",
        disease="NSCLC",
        config={"scenario": "general"},
    )
    result = run(ctx)
    ta = result.previous["target_assessment"]
    assert ta["total_score"] == 82.5
    assert ta["grade"] == "A"
    assert mock_run_assessment.called


@patch("target_assessment.assessment_core.run_assessment")
def test_target_assessment_defaults_disease(mock_run_assessment):
    mock_run_assessment.return_value = {"total_score": 50, "grade": "C"}
    ctx = PipelineContext(
        job_id="test-001", gene_symbol="BRCA1", disease=None, config={}
    )
    result = run(ctx)
    called_disease = mock_run_assessment.call_args[1]["disease"]
    assert called_disease == "pan-cancer"
