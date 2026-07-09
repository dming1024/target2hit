"""Ligand preparation: SMILES → 3D conformer → PDBQT."""
from __future__ import annotations
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


def prepare_ligand(smiles: str, compound_id: str, work_dir: Path | None = None) -> Path:
    """Convert SMILES to PDBQT for AutoDock Vina using RDKit + Meeko."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    work_dir = work_dir or Path(tempfile.mkdtemp(prefix="dock_"))
    work_dir.mkdir(parents=True, exist_ok=True)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES for {compound_id}: {smiles}")

    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    status = AllChem.EmbedMolecule(mol, params)
    if status != 0:
        AllChem.EmbedMolecule(mol, AllChem.ETKDG())
    AllChem.MMFFOptimizeMolecule(mol)

    try:
        from meeko import MoleculePreparation, PDBQTWriterLegacy
        preparator = MoleculePreparation()
        mol_setup = preparator.prepare(mol)
        pdbqt_string, _ = PDBQTWriterLegacy.write_string(mol_setup)
        pdbqt_path = work_dir / f"{compound_id}.pdbqt"
        pdbqt_path.write_text(pdbqt_string)
        return pdbqt_path
    except ImportError:
        logger.warning("Meeko not available, using OpenBabel for PDBQT conversion")
        mol2_path = work_dir / f"{compound_id}.mol2"
        Chem.MolToMol2File(mol, str(mol2_path))
        pdbqt_path = work_dir / f"{compound_id}.pdbqt"
        import subprocess
        subprocess.run(
            ["obabel", str(mol2_path), "-O", str(pdbqt_path), "--gen3d"],
            capture_output=True, timeout=60,
        )
        return pdbqt_path
