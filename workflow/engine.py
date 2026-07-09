"""WorkflowEngine orchestrates modules in registration order."""
from __future__ import annotations
import logging
import time
from typing import List, Protocol, Tuple
from workflow.contracts import PipelineContext

logger = logging.getLogger(__name__)


class PipelineModule(Protocol):
    """Protocol for pipeline modules."""
    def run(self, ctx: PipelineContext) -> PipelineContext:
        ...


class WorkflowEngine:
    """Orchestrates pipeline modules sequentially.

    Modules are registered with a name and run in registration order.
    Each module receives PipelineContext and returns updated PipelineContext.
    On failure, partial results are preserved for debugging.
    """

    def __init__(self, preserve_partial: bool = True):
        self._modules: List[Tuple[str, PipelineModule]] = []
        self._preserve_partial_results = preserve_partial

    def register(self, name: str, module: PipelineModule) -> None:
        """Register a module. Modules run in registration order."""
        self._modules.append((name, module))

    def run(self, ctx: PipelineContext) -> PipelineContext:
        """Run all registered modules sequentially.

        Args:
            ctx: Initial PipelineContext with job_id, gene_symbol, disease, config.

        Returns:
            PipelineContext with all module outputs in ctx.previous.

        Raises:
            RuntimeError: If any module fails, preserving partial results.
        """
        for name, module in self._modules:
            logger.info(f"[{ctx.job_id}] Starting module: {name}")
            t0 = time.monotonic()
            try:
                ctx = module.run(ctx)
                elapsed = time.monotonic() - t0
                logger.info(f"[{ctx.job_id}] Module {name} completed in {elapsed:.1f}s")
            except Exception as e:
                logger.error(f"[{ctx.job_id}] Module {name} failed: {e}")
                if self._preserve_partial_results:
                    logger.info(f"[{ctx.job_id}] Preserving partial results from {len(ctx.previous)} modules")
                    ctx = PipelineContext(
                        job_id=ctx.job_id,
                        gene_symbol=ctx.gene_symbol,
                        disease=ctx.disease,
                        config=ctx.config,
                        previous={**ctx.previous, f"_error_{name}": str(e)},
                    )
                raise RuntimeError(f"Module {name} failed: {e}") from e
        return ctx
