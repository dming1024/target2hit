"""AutoDock Vina runner."""
from __future__ import annotations
import logging
import subprocess
import tempfile
from pathlib import Path
from workflow.contracts import DockedPose, Pocket

logger = logging.getLogger(__name__)


def prepare_receptor(pdb_path: Path, work_dir: Path) -> Path:
    """Convert receptor PDB to PDBQT using OpenBabel."""
    pdbqt_path = work_dir / f"{pdb_path.stem}.pdbqt"
    result = subprocess.run(
        ["obabel", str(pdb_path), "-O", str(pdbqt_path), "-xr"],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Receptor preparation failed: {result.stderr}")
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
