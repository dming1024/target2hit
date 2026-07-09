"""Clean and prepare protein structures for docking."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

_AA_MAP = {
    "ALA": "A", "ARG": "R", "ASN": "N", "ASP": "D", "CYS": "C",
    "GLN": "Q", "GLU": "E", "GLY": "G", "HIS": "H", "ILE": "I",
    "LEU": "L", "LYS": "K", "MET": "M", "PHE": "F", "PRO": "P",
    "SER": "S", "THR": "T", "TRP": "W", "TYR": "Y", "VAL": "V",
}


def clean_pdb(pdb_path: Path) -> Tuple[Path, str]:
    """Clean a PDB file: remove water, extract sequence."""
    from Bio.PDB import PDBParser, PDBIO
    from Bio.SeqUtils import seq1

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("protein", str(pdb_path))

    # Remove waters
    for model in structure:
        for chain in model:
            chain.child_list = [r for r in chain if r.get_resname() != "HOH"]

    io = PDBIO()
    io.set_structure(structure)
    cleaned_path = pdb_path.parent / f"{pdb_path.stem}_clean.pdb"
    io.save(str(cleaned_path))

    # Extract sequence from first chain
    model = structure[0]
    chain = list(model.get_chains())[0]
    residues = [r for r in chain if r.get_resname() != "HOH"]
    sequence = "".join([seq1(r.get_resname()) for r in residues if r.get_resname() in _AA_MAP])

    return cleaned_path, sequence
