"""Tests for docking module."""
from pathlib import Path
from unittest.mock import patch
from workflow.contracts import (
    PipelineContext, StructureResult, PocketResult, Pocket,
    ScreeningResult, ScoredCompound, DockingResult, DockedPose,
)
from docking import run


@patch("docking.dock_parallel")
@patch("docking.prepare_ligand")
@patch("docking.prepare_receptor")
def test_docking_module(mock_prep_receptor, mock_prep_ligand, mock_dock_parallel):
    mock_prep_receptor.return_value = Path("/tmp/receptor.pdbqt")
    mock_prep_ligand.return_value = Path("/tmp/ligand.pdbqt")
    mock_dock_parallel.return_value = [
        DockedPose("C001", -8.5, Path("/tmp/pose1.pdbqt")),
        DockedPose("C002", -7.2, Path("/tmp/pose2.pdbqt")),
    ]

    ctx = PipelineContext(
        job_id="test-001",
        gene_symbol="EGFR",
        disease=None,
        config={"docking": {"exhaustiveness": 8, "num_cpus": 2, "box_padding": 4.0}},
        previous={
            "structure": StructureResult(
                pdb_path=Path("/tmp/egfr_clean.pdb"),
                protein_sequence="MPSK", source="pdb", uniprot_id="P00533",
            ),
            "pocket": PocketResult(pockets=[
                Pocket(rank=1, center=(10.0, 20.0, 30.0),
                       size=(20.0, 20.0, 20.0), druggability_score=0.85, volume=450.0)
            ]),
            "screening": ScreeningResult(ranked_compounds=[
                ScoredCompound("C001", "CC(=O)O", 0.9),
                ScoredCompound("C002", "CC(C)C(=O)O", 0.7),
            ]),
        },
    )

    result = run(ctx)
    dr = result.previous["docking"]
    assert isinstance(dr, DockingResult)
    assert len(dr.poses) == 2
    assert dr.poses[0].binding_energy == -8.5
    mock_prep_receptor.assert_called_once()
    assert mock_prep_ligand.call_count == 2
    mock_dock_parallel.assert_called_once()
