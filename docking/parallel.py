"""Parallel docking execution via ProcessPoolExecutor."""
from __future__ import annotations
import logging
from pathlib import Path
from typing import List
from concurrent.futures import ProcessPoolExecutor, as_completed
from workflow.contracts import DockedPose, Pocket
from docking.vina import dock_single

logger = logging.getLogger(__name__)


def dock_parallel(
    receptor_pdbqt: Path,
    ligand_pdbqts: List[Path],
    pocket: Pocket,
    exhaustiveness: int = 8,
    box_padding: float = 4.0,
    num_workers: int = 4,
) -> List[DockedPose]:
    """Run AutoDock Vina in parallel for multiple ligands."""
    results: List[DockedPose] = []
    total = len(ligand_pdbqts)

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = {}
        for lp in ligand_pdbqts:
            future = executor.submit(
                dock_single, receptor_pdbqt, lp, pocket, exhaustiveness, box_padding
            )
            futures[future] = lp

        for i, future in enumerate(as_completed(futures)):
            try:
                pose = future.result()
                results.append(pose)
            except Exception as e:
                lp = futures[future]
                logger.error(f"Docking failed for {lp.stem}: {e}")
                results.append(DockedPose(
                    compound_id=lp.stem, binding_energy=0.0, pose_file=lp,
                ))
            if (i + 1) % 50 == 0:
                logger.info(f"Docking progress: {i+1}/{total}")

    results.sort(key=lambda p: p.binding_energy)
    return results
