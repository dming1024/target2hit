"""Ligand preparation: SMILES → 3D conformer → PDBQT."""
from __future__ import annotations
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


def prepare_ligand(smiles: str, compound_id: str, work_dir: Path | None = None) -> Path:
    """Convert SMILES to PDBQT for AutoDock Vina.

    Tries Meeko first (best quality), then OpenBabel, then pure Python.
    """
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

    # 1) Meeko
    try:
        from meeko import MoleculePreparation, PDBQTWriterLegacy
        preparator = MoleculePreparation()
        mol_setup = preparator.prepare(mol)
        if isinstance(mol_setup, list):
            mol_setup = mol_setup[0]
        result = PDBQTWriterLegacy.write_string(mol_setup)
        pdbqt_string = result[0]
        pdbqt_path = work_dir / f"{compound_id}.pdbqt"
        pdbqt_path.write_text(pdbqt_string)
        return pdbqt_path
    except Exception:
        logger.debug("Meeko unavailable", exc_info=True)

    # 2) OpenBabel
    try:
        import subprocess
        mol2_path = work_dir / f"{compound_id}.mol2"
        mol2_text = Chem.MolToMol2Block(mol) if hasattr(Chem, "MolToMol2Block") else ""
        if mol2_text:
            mol2_path.write_text(mol2_text)
        pdbqt_path = work_dir / f"{compound_id}.pdbqt"
        result = subprocess.run(
            ["obabel", str(mol2_path), "-O", str(pdbqt_path), "--gen3d"],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode == 0:
            return pdbqt_path
    except Exception:
        logger.debug("OpenBabel unavailable", exc_info=True)

    # 3) Pure Python fallback
    logger.warning("Meeko and OpenBabel both unavailable, using pure-Python PDBQT writer")
    pdbqt_path = work_dir / f"{compound_id}.pdbqt"
    _write_pdbqt_python(mol, pdbqt_path)
    return pdbqt_path


def _write_pdbqt_python(mol, path: Path) -> None:
    """Pure Python PDBQT writer — computes Gasteiger charges and assigns
    AutoDock4 atom types. Always works, no external deps beyond RDKit."""
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.RemoveHs(mol)  # Vina adds its own hydrogens
    AllChem.ComputeGasteigerCharges(mol)
    conf = mol.GetConformer()

    lines = []
    for i, atom in enumerate(mol.GetAtoms(), start=1):
        pos = conf.GetAtomPosition(atom.GetIdx())
        ad4_type = _assign_atom_type(atom)
        charge = float(atom.GetDoubleProp("_GasteigerCharge")) if ad4_type else 0.0

        # PDB format with charge (cols 71-76) and atom type (cols 78-79)
        line = (
            f"HETATM{i:>5} {atom.GetSymbol():^4}  LIG     1    "
            f"{pos.x:8.3f}{pos.y:8.3f}{pos.z:8.3f}"
            f"  1.00  0.00    {charge:>6.3f} {ad4_type}"
        )
        lines.append(line)

    lines.append("END")
    path.write_text("\n".join(lines))


def _assign_atom_type(atom) -> str:
    """Map an RDKit atom to its AutoDock4 type."""
    atomic_num = atom.GetAtomicNum()
    is_aromatic = atom.GetIsAromatic()
    degree = atom.GetDegree()
    h = atom.GetTotalNumHs()

    if atomic_num == 6:  # Carbon
        return "A" if is_aromatic else "C"
    if atomic_num == 7:  # Nitrogen
        if h > 0 or degree == 2:
            return "NA"
        return "N"
    if atomic_num == 8:  # Oxygen
        return "OA"
    if atomic_num == 16:  # Sulfur
        return "SA"
    if atomic_num == 15:  # Phosphorus
        return "P"
    if atomic_num == 9:
        return "F"
    if atomic_num == 17:
        return "Cl"
    if atomic_num == 35:
        return "Br"
    if atomic_num == 53:
        return "I"
    return "C"  # fallback
