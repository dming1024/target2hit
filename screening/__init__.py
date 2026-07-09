"""AI Virtual Screening module."""
from __future__ import annotations
import logging
from workflow.contracts import PipelineContext, ScreeningConfig, ScreeningResult
from screening.compound_library import CompoundLibrary
from screening.zero_shot import run_zero_shot_screening

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Run AI virtual screening on the target."""
    screening_cfg = ctx.config.get("screening", {})
    lib_cfg = ctx.config.get("compound_library", {})

    config = ScreeningConfig(
        mode=screening_cfg.get("mode", "zero_shot"),
        protein_model=screening_cfg.get("protein_model", "esm2_t30_150M_UR50D"),
        ligand_model=screening_cfg.get("ligand_model", "ChemBERTa-77M-MLM"),
        mlp_weights=screening_cfg.get("mlp_weights"),
        projection_dim=screening_cfg.get("projection_dim", 256),
        batch_size=screening_cfg.get("batch_size", 256),
        top_n=screening_cfg.get("top_n", 500),
        device=screening_cfg.get("device", "auto"),
    )

    library = CompoundLibrary(max_compounds=lib_cfg.get("max_compounds", 100000))
    library.load_sample()

    protein_seq = ctx.previous["structure"].protein_sequence

    if config.mode == "zero_shot":
        result = run_zero_shot_screening(protein_seq, library, config)
    elif config.mode == "mlp":
        from screening.mlp_head import MLPPredictor
        predictor = MLPPredictor(config.mlp_weights)
        raise NotImplementedError("MLP mode requires trained weights. Use mode='zero_shot' for V1.")
    else:
        raise ValueError(f"Unknown screening mode: {config.mode}")

    new_previous = dict(ctx.previous)
    new_previous["screening"] = result
    return PipelineContext(
        job_id=ctx.job_id,
        gene_symbol=ctx.gene_symbol,
        disease=ctx.disease,
        config=ctx.config,
        previous=new_previous,
    )
