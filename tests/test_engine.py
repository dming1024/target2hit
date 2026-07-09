"""Tests for workflow engine."""
import pytest
from workflow.contracts import PipelineContext
from workflow.engine import WorkflowEngine


class FakeModule:
    """A fake module that returns a predictable result."""
    def __init__(self, name: str, result_key: str, should_fail: bool = False):
        self.name = name
        self.result_key = result_key
        self.should_fail = should_fail
        self.called = False

    def run(self, ctx: PipelineContext) -> PipelineContext:
        self.called = True
        if self.should_fail:
            raise RuntimeError(f"FakeModule {self.name} failed")
        new_previous = dict(ctx.previous)
        new_previous[self.result_key] = f"{self.name}_output"
        return PipelineContext(
            job_id=ctx.job_id,
            gene_symbol=ctx.gene_symbol,
            disease=ctx.disease,
            config=ctx.config,
            previous=new_previous,
        )


class TestWorkflowEngine:
    def test_runs_modules_in_order(self):
        engine = WorkflowEngine()
        mod_a = FakeModule("module_a", "result_a")
        mod_b = FakeModule("module_b", "result_b")
        engine.register("module_a", mod_a)
        engine.register("module_b", mod_b)

        ctx = PipelineContext(
            job_id="test-001", gene_symbol="EGFR", disease=None, config={}
        )
        result = engine.run(ctx)

        assert mod_a.called
        assert mod_b.called
        assert result.previous["result_a"] == "module_a_output"
        assert result.previous["result_b"] == "module_b_output"

    def test_failed_module_stops_pipeline_and_raises(self):
        engine = WorkflowEngine(preserve_partial=False)
        mod_a = FakeModule("module_a", "result_a")
        mod_bad = FakeModule("bad_module", "bad", should_fail=True)
        mod_c = FakeModule("module_c", "result_c")

        engine.register("module_a", mod_a)
        engine.register("bad_module", mod_bad)
        engine.register("module_c", mod_c)

        ctx = PipelineContext(
            job_id="test-001", gene_symbol="EGFR", disease=None, config={}
        )
        with pytest.raises(RuntimeError, match="Module bad_module failed"):
            engine.run(ctx)

        assert mod_a.called
        assert mod_bad.called
        assert not mod_c.called

    def test_preserve_partial_results_on_failure(self):
        engine = WorkflowEngine(preserve_partial=True)
        mod_a = FakeModule("module_a", "result_a")
        mod_bad = FakeModule("bad", "bad", should_fail=True)

        engine.register("module_a", mod_a)
        engine.register("bad", mod_bad)

        ctx = PipelineContext(
            job_id="test-001", gene_symbol="EGFR", disease=None, config={}
        )
        with pytest.raises(RuntimeError, match="Module bad failed"):
            engine.run(ctx)

        # Partial execution preserved: module_a ran successfully before the failure
        assert mod_a.called
        assert mod_bad.called

    def test_empty_engine_returns_unchanged_context(self):
        engine = WorkflowEngine()
        ctx = PipelineContext(
            job_id="test-001", gene_symbol="EGFR", disease=None, config={}
        )
        result = engine.run(ctx)
        assert result.job_id == ctx.job_id
        assert result.previous == {}
