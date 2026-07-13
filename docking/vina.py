"""AutoDock Vina runner."""
from __future__ import annotations
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple
from workflow.contracts import DockedPose, Pocket

logger = logging.getLogger(__name__)

# AutoDock4 atom-type mapping for protein residues
# Based on AD4_parameters.dat standard assignments
_AD4_ATOM_TYPE = {}  # built lazily in _build_atom_type_map()


def _build_atom_type_map() -> dict:
    """Build a (resname, atom_name) → AD4_type lookup for standard residues."""
    if _AD4_ATOM_TYPE:
        return _AD4_ATOM_TYPE

    # Standard mapping by element and context
    backbone_types = {"N": "N", "CA": "C", "C": "C", "O": "OA",
                      "H": "HD", "HA": "H", "HN": "HD"}
    # Sidechain: residue → {atom: type}
    sidechain_defaults = {
        "CB": "C", "CG": "C", "CG1": "C", "CG2": "C",
        "CD": "C", "CD1": "C", "CD2": "C", "CE": "C", "CE1": "C", "CE2": "C", "CZ": "C",
    }
    special = {
        # Aromatic carbons
        "PHE": {"CG": "A", "CD1": "A", "CD2": "A", "CE1": "A", "CE2": "A", "CZ": "A"},
        "TYR": {"CG": "A", "CD1": "A", "CD2": "A", "CE1": "A", "CE2": "A", "CZ": "A"},
        "TRP": {"CG": "A", "CD1": "A", "CD2": "A", "CE2": "A", "CE3": "A", "CZ2": "A", "CZ3": "A", "CH2": "A"},
        "HIS": {"CG": "A", "CD2": "A", "CE1": "A", "ND1": "NA"},
        # Oxygens
        "SER": {"OG": "OA"}, "THR": {"OG1": "OA"},
        "ASP": {"OD1": "OA", "OD2": "OA"}, "ASN": {"OD1": "OA"},
        "GLU": {"OE1": "OA", "OE2": "OA"}, "GLN": {"OE1": "OA"},
        "TYR": {"OH": "OA"},
        # Nitrogens
        "LYS": {"NZ": "N"}, "ARG": {"NE": "N", "NH1": "N", "NH2": "N"},
        "ASN": {"ND2": "N"}, "GLN": {"NE2": "N"},
        "HIS": {"NE2": "NA"}, "TRP": {"NE1": "NA"},
        # Sulfurs
        "CYS": {"SG": "SA"}, "MET": {"SD": "SA"},
    }

    _AD4_ATOM_TYPE.update(backbone_types)
    for res, atoms in special.items():
        for atom, atype in atoms.items():
            _AD4_ATOM_TYPE[(res, atom)] = atype

    # also store sidechain defaults
    _AD4_ATOM_TYPE["_sidechain_defaults"] = sidechain_defaults
    return _AD4_ATOM_TYPE


def _resolve_ad4_type(resname: str, atom_name: str, element: str) -> str:
    """Map a protein atom to its AutoDock4 type."""
    type_map = _build_atom_type_map()
    key = (resname.upper(), atom_name.strip().upper())
    if key in type_map:
        return type_map[key]

    # Hydrogen rules
    if element == "H":
        return "HD" if atom_name.strip().upper().startswith("H") else "H"

    # Carbon default
    if element == "C":
        defaults = type_map.get("_sidechain_defaults", {})
        return defaults.get(atom_name.strip().upper(), "C")
    if element in ("O", "OXT"):
        return "OA"
    if element == "N":
        return "N"
    if element == "S":
        return "SA"
    if element == "P":
        return "P"
    # Fallback
    return "C"


_DEFAULT_CHARGES = {"C": 0.0, "A": 0.0, "N": -0.3, "NA": -0.3,
                    "OA": -0.4, "SA": -0.2, "HD": 0.2, "H": 0.1,
                    "P": 0.5, "F": -0.2, "Cl": -0.2, "Br": -0.2, "I": -0.1}


def _parse_pdb_atom_line(line: str) -> Tuple[str, str, str, str, str, float, float, float, str, str]:
    """Parse a PDB ATOM/HETATM record. Returns (record, serial, atom, resname, chain, x, y, z, element, alt)."""
    record = line[0:6].strip()
    if record not in ("ATOM", "HETATM"):
        return None
    serial = line[6:11].strip()
    atom = line[12:16].strip()
    alt = line[16:17].strip()
    resname = line[17:20].strip()
    chain = line[21:22].strip()
    try:
        x = float(line[30:38].strip())
        y = float(line[38:46].strip())
        z = float(line[46:54].strip())
    except ValueError:
        return None
    element = line[76:78].strip() or atom[0]
    return record, serial, atom, resname, chain, x, y, z, element, alt


def prepare_receptor(pdb_path: Path, work_dir: Path) -> Path:
    """Convert receptor PDB to PDBQT.

    Tries OpenBabel first, falls back to pure-Python converter (Windows-friendly).
    """
    pdbqt_path = work_dir / f"{pdb_path.stem}.pdbqt"

    # Try OpenBabel first
    try:
        result = subprocess.run(
            ["obabel", str(pdb_path), "-O", str(pdbqt_path), "-xr"],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode == 0:
            logger.info("Receptor prepared with OpenBabel")
            return pdbqt_path
        logger.warning(f"OpenBabel failed: {result.stderr[:200]}, using pure Python fallback")
    except FileNotFoundError:
        logger.info("OpenBabel not found, using pure Python receptor preparation")
    except Exception:
        logger.info("OpenBabel unavailable, using pure Python receptor preparation")

    return _prepare_receptor_python(pdb_path, pdbqt_path)


def _prepare_receptor_python(pdb_path: Path, pdbqt_path: Path) -> Path:
    """Pure Python PDB → PDBQT conversion for receptor. No external deps."""
    pdblines = pdb_path.read_text().splitlines()
    pdbqt_lines: List[str] = []
    atom_serial = 0
    last_serial = 0

    for line in pdblines:
        if line.startswith("END"):
            break
        if not line.startswith(("ATOM", "HETATM")):
            if line.startswith("TER"):
                pdbqt_lines.append("TER")
            continue

        parsed = _parse_pdb_atom_line(line)
        if parsed is None:
            continue

        record, serial, atom_name, resname, chain, x, y, z, element, alt = parsed
        atom_serial += 1

        ad4_type = _resolve_ad4_type(resname, atom_name, element)
        charge = _DEFAULT_CHARGES.get(ad4_type, 0.0)

        # PDBQT format: same as PDB but charge at cols 71-76, atom type at cols 78-79
        # ATOM  <serial> <atom> <res> <chain> <resi>   <x>     <y>     <z>   <occ> <bfactor>  <charge>  <type>
        pdbqt_line = (
            f"{record:<6}{atom_serial:>5} {atom_name:^4}{alt:1}{resname:>3} "
            f"{chain:1}{1:>4}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}"
            f"  1.00  0.00"
            f"    {charge:>6.3f} {ad4_type}"
        )
        pdbqt_lines.append(pdbqt_line)
        last_serial = atom_serial

    pdbqt_lines.append("TER")
    pdbqt_lines.append("END")
    pdbqt_path.write_text("\n".join(pdbqt_lines))
    logger.info(f"Prepared receptor PDBQT ({last_serial} atoms) via pure Python")
    return pdbqt_path


def dock_single(
    receptor_pdbqt: Path,
    ligand_pdbqt: Path,
    pocket: Pocket,
    exhaustiveness: int = 8,
    box_padding: float = 4.0,
) -> DockedPose:
    """Run AutoDock Vina for a single ligand."""
    cx, cy, cz = pocket.center
    sx, sy, sz = [s + box_padding for s in pocket.size]

    out_dir = Path(tempfile.mkdtemp(prefix="vina_out_"))
    out_pdbqt = out_dir / f"{ligand_pdbqt.stem}_out.pdbqt"

    cmd = [
        "vina",
        "--receptor", str(receptor_pdbqt),
        "--ligand", str(ligand_pdbqt),
        "--center_x", str(cx), "--center_y", str(cy), "--center_z", str(cz),
        "--size_x", str(sx), "--size_y", str(sy), "--size_z", str(sz),
        "--exhaustiveness", str(exhaustiveness),
        "--out", str(out_pdbqt),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        logger.error(f"Vina failed: {result.stderr}")
        return DockedPose(
            compound_id=ligand_pdbqt.stem, binding_energy=0.0, pose_file=out_pdbqt,
        )

    energy = _parse_vina_output(result.stdout)
    return DockedPose(
        compound_id=ligand_pdbqt.stem.replace("_out", ""),
        binding_energy=energy,
        pose_file=out_pdbqt,
    )


def _parse_vina_output(stdout: str) -> float:
    """Extract best binding energy from Vina stdout."""
    for line in stdout.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 2:
            try:
                return float(parts[0])
            except ValueError:
                continue
    return 0.0
