"""Tests for report module."""
from pathlib import Path
from workflow.contracts import (
    PipelineContext, RankingResult, RankedHit, ScreeningResult, ScoredCompound,
    DockingResult, DockedPose, StructureResult, PocketResult, Pocket,
    AnnotationResult, ReportResult,
)
from report import run


def test_report_generation(tmp_path):
    ctx = PipelineContext(
        job_id="test-001", gene_symbol="EGFR", disease="NSCLC",
        config={"report": {"output_dir": str(tmp_path)}},
        previous={
            "target_assessment": {"total_score": 82.5, "grade": "A"},
            "structure": StructureResult(
                pdb_path=Path("/tmp/test.pdb"), protein_sequence="MPSK",
                source="pdb", resolution=2.1, uniprot_id="P00533",
            ),
            "pocket": PocketResult(pockets=[
                Pocket(rank=1, center=(0, 0, 0), size=(20, 20, 20), druggability_score=0.85, volume=450)
            ]),
            "screening": ScreeningResult(ranked_compounds=[
                ScoredCompound("C001", "CC(=O)O", 0.9),
                ScoredCompound("C002", "CC(C)C(=O)O", 0.7),
            ]),
            "docking": DockingResult(poses=[
                DockedPose("C001", -8.5, Path("/tmp/pose1.pdbqt")),
                DockedPose("C002", -7.2, Path("/tmp/pose2.pdbqt")),
            ]),
            "ranking": RankingResult(hits=[
                RankedHit(rank=1, compound_id="C001", smiles="CC(=O)O",
                          final_score=0.9, ai_score=0.9, dock_score=-8.5,
                          drug_likeness=0.8, sa_score=0.1, pains_flag=False),
                RankedHit(rank=2, compound_id="C002", smiles="CC(C)C(=O)O",
                          final_score=0.7, ai_score=0.7, dock_score=-7.2,
                          drug_likeness=0.6, sa_score=0.2, pains_flag=False),
            ]),
            "annotation": AnnotationResult(annotations={"C001": {"pubchem_cid": "2244"}, "C002": {}}),
        },
    )
    result = run(ctx)
    rr = result.previous["report"]
    assert isinstance(rr, ReportResult)
    assert rr.report_json.exists()
