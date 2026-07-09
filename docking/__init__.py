"""Molecular Docking module."""
from __future__ import annotations
import logging
from pathlib import Path
import tempfile
from workflow.contracts import PipelineContext, DockingResult, Pocket
from docking.ligand_prep import prepare_ligand
from docking.vina import prepare_receptor
from docking.parallel import dock_parallel

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Run molecular docking for top screening compounds."""
    docking_cfg = ctx.config.get("docking", {})

    struct = ctx.previous["structure"]
    pocket: Pocket = ctx.previous["pocket"].pockets[0]
    screening = ctx.previous["screening"]
    top_compounds = screening.ranked_compounds[:docking_cfg.get("top_n", 100)]

    work_dir = Path(tempfile.mkdtemp(prefix="docking_"))
    logger.info(f"[{ctx.job_id}] Docking {len(top_compounds)} compounds in {work_dir}")

    receptor_pdbqt = prepare_receptor(struct.pdb_path, work_dir)

    ligand_pdbqts = []
    for c in top_compounds:
        try:
            lp = prepare_ligand(c.smiles, c.compound_id, work_dir / "ligands")
            ligand_pdbqts.append(lp)
        except Exception as e:
            logger.warning(f"Failed to prepare {c.compound_id}: {e}")

    poses = dock_parallel(
        receptor_pdbqt=receptor_pdbqt,
        ligand_pdbqts=ligand_pdbqts,
        pocket=pocket,
        exhaustiveness=docking_cfg.get("exhaustiveness", 8),
        box_padding=docking_cfg.get("box_padding", 4.0),
        num_workers=docking_cfg.get("num_cpus", 4),
    )

    result = DockingResult(poses=poses)

    new_previous = dict(ctx.previous)
    new_previous["docking"] = result
    return PipelineContext(
        job_id=ctx.job_id,
        gene_symbol=ctx.gene_symbol,
        disease=ctx.disease,
        config=ctx.config,
        previous=new_previous,
    )
