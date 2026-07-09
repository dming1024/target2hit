"""fPocket wrapper for pocket detection."""
from __future__ import annotations
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple
from workflow.contracts import Pocket

logger = logging.getLogger(__name__)


def run_fpocket(pdb_path: Path, top_n: int = 3) -> List[Pocket]:
    """Run fPocket on a PDB file and return top N pockets."""
    import shutil
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        work_pdb = tmpdir / pdb_path.name
        shutil.copy(pdb_path, work_pdb)

        try:
            result = subprocess.run(
                ["fpocket", "-f", str(work_pdb)],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(tmpdir),
            )
            if result.returncode != 0:
                logger.warning(f"fPocket returned non-zero: {result.stderr}")
        except FileNotFoundError:
            logger.warning("fPocket not installed, returning empty pockets")
            return []

        pocket_dir = tmpdir / f"{pdb_path.stem}_out"
        if not pocket_dir.exists():
            logger.warning(f"fPocket output not found at {pocket_dir}")
            return []

        pockets = _parse_fpocket_output(pocket_dir)
        pockets.sort(key=lambda p: p.druggability_score, reverse=True)
        return pockets[:top_n]


def _parse_fpocket_output(pocket_dir: Path) -> List[Pocket]:
    """Parse fPocket *_info.txt files."""
    pockets = []
    info_files = sorted(pocket_dir.glob("*_info.txt"))
    for rank, info_file in enumerate(info_files, start=1):
        try:
            center, score, volume = _parse_info_file(info_file)
            pockets.append(Pocket(
                rank=rank,
                center=center,
                size=(20.0, 20.0, 20.0),  # default box size
                druggability_score=score,
                volume=volume,
            ))
        except Exception as e:
            logger.warning(f"Failed to parse {info_file}: {e}")
    return pockets


def _parse_info_file(path: Path) -> Tuple[Tuple[float, float, float], float, float]:
    """Parse a single fPocket info file."""
    center = (0.0, 0.0, 0.0)
    score = 0.5
    volume = 0.0
    with open(path) as f:
        for line in f:
            if "Centroid" in line:
                parts = line.split(":")[1].strip().split()
                center = tuple(float(x) for x in parts[:3])
            if "Druggability Score" in line:
                score = float(line.split(":")[1].strip())
            if "Volume" in line:
                volume = float(line.split(":")[1].strip())
    return center, score, volume
