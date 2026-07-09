"""Structure preparation module."""
from __future__ import annotations
import logging
from workflow.contracts import PipelineContext, StructureResult
from structure.resolver import resolve_uniprot, search_pdb, download_structure
from structure.preparation import clean_pdb

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Resolve gene → structure."""
    struct_cfg = ctx.config.get("structure", {})
    prefer_pdb = struct_cfg.get("prefer_experimental", True)
    max_res = struct_cfg.get("max_resolution", 3.0)

    uniprot_id = resolve_uniprot(ctx.gene_symbol)
    logger.info(f"[{ctx.job_id}] Resolved {ctx.gene_symbol} → UniProt:{uniprot_id}")

    pdb_info = None
    if prefer_pdb:
        pdb_info = search_pdb(uniprot_id, max_resolution=max_res)

    pdb_path, source = download_structure(pdb_info, uniprot_id)
    cleaned_path, sequence = clean_pdb(pdb_path)

    resolution = pdb_info["resolution"] if pdb_info else None
    result = StructureResult(
        pdb_path=cleaned_path,
        protein_sequence=sequence,
        source=source,
        resolution=resolution,
        uniprot_id=uniprot_id,
    )

    new_previous = dict(ctx.previous)
    new_previous["structure"] = result
    return PipelineContext(
        job_id=ctx.job_id,
        gene_symbol=ctx.gene_symbol,
        disease=ctx.disease,
        config=ctx.config,
        previous=new_previous,
    )
