"""Tests for database models."""
from database.models import Job, Compound, ScreeningResult, DockingResult, RankingResult


def test_job_model():
    job = Job(id="test-001", gene_symbol="EGFR", disease="NSCLC", status="pending")
    assert job.status == "pending"
    assert job.gene_symbol == "EGFR"


def test_compound_model():
    c = Compound(id="CHEMBL123", smiles="CC(=O)O", molecular_weight=180.16)
    assert c.smiles == "CC(=O)O"


def test_all_models_import():
    models = [Job, Compound, ScreeningResult, DockingResult, RankingResult]
    for model in models:
        assert hasattr(model, "__tablename__")
