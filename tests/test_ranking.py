"""Tests for consensus ranking module."""
from pathlib import Path
from workflow.contracts import (
    PipelineContext, ScreeningResult, ScoredCompound,
    DockingResult, DockedPose, RankingResult,
)
from ranking import run


def test_consensus_ranking():
    ctx = PipelineContext(
        job_id="test-001",
        gene_symbol="EGFR",
        disease=None,
        config={"ranking": {"weights": {"ai_score": 0.30, "dock_score": 0.30, "drug_likeness": 0.15, "novelty": 0.10, "sa_penalty": 0.10, "pains_penalty": 0.05}}},
        previous={
            "screening": ScreeningResult(ranked_compounds=[
                ScoredCompound("C001", "CC(=O)OC1=CC=CC=C1C(=O)O", 0.9),
                ScoredCompound("C002", "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", 0.7),
            ]),
            "docking": DockingResult(poses=[
                DockedPose("C001", -8.5, Path("/tmp/pose1.pdbqt")),
                DockedPose("C002", -7.2, Path("/tmp/pose2.pdbqt")),
            ]),
        },
    )
    result = run(ctx)
    rr = result.previous["ranking"]
    assert isinstance(rr, RankingResult)
    assert len(rr.hits) == 2
    assert rr.hits[0].compound_id == "C001"
    assert rr.hits[0].final_score > 0
    assert rr.hits[0].drug_likeness > 0
    assert rr.hits[0].rank == 1
    assert rr.hits[1].rank == 2
