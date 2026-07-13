"""Report generation module."""
from __future__ import annotations
import logging
import tempfile
from pathlib import Path
from workflow.contracts import PipelineContext
from report.generator import generate_report

logger = logging.getLogger(__name__)


def run(ctx: PipelineContext) -> PipelineContext:
    """Generate pipeline report."""
    report_cfg = ctx.config.get("report", {})
    default_dir = Path(tempfile.gettempdir()) / "target2drug" / ctx.job_id
    output_dir = Path(report_cfg.get("output_dir", str(default_dir)))

    result = generate_report(ctx, output_dir)

    new_previous = dict(ctx.previous)
    new_previous["report"] = result
    return PipelineContext(
        job_id=ctx.job_id, gene_symbol=ctx.gene_symbol,
        disease=ctx.disease, config=ctx.config, previous=new_previous,
    )
