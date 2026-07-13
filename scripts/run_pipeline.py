#!/usr/bin/env python3
"""CLI entry point for running the Target2Hit pipeline."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Target2Hit Discovery Pipeline")
    parser.add_argument("--gene", "-g", required=True, help="Gene symbol (e.g., EGFR)")
    parser.add_argument("--disease", "-d", default=None, help="Disease context (e.g., NSCLC)")
    parser.add_argument("--config", "-c", default=None, help="YAML config override")
    parser.add_argument("--output", "-o", default="/tmp/target2drug", help="Output directory")
    args = parser.parse_args()

    import uuid
    from workflow.config import load_config
    from workflow.contracts import PipelineContext
    from workflow.engine import WorkflowEngine

    job_id = str(uuid.uuid4())[:8]
    config = load_config(args.config)
    config["report"]["output_dir"] = args.output

    ctx = PipelineContext(
        job_id=job_id,
        gene_symbol=args.gene,
        disease=args.disease,
        config=config,
    )

    import target_assessment, structure, pocket, screening, docking, ranking, annotation, report

    engine = WorkflowEngine(preserve_partial=True)
    engine.register("target_assessment", target_assessment)
    engine.register("structure", structure)
    engine.register("pocket", pocket)
    engine.register("screening", screening)
    engine.register("docking", docking)
    engine.register("ranking", ranking)
    engine.register("annotation", annotation)
    engine.register("report", report)

    print(f"Job {job_id}: {args.gene} → Hits pipeline starting...")
    try:
        result = engine.run(ctx)
        ranking = result.previous.get("ranking")
        if ranking and ranking.hits:
            print(f"\nTop 5 Hits for {args.gene}:")
            for hit in ranking.hits[:5]:
                print(f"  {hit.rank}. {hit.compound_id}: {hit.final_score:.4f} "
                      f"(AI: {hit.ai_score:.3f}, Dock: {hit.dock_score:.1f})")
        report = result.previous.get("report")
        if report:
            print(f"\nReport: {report.report_json}")
    except RuntimeError as e:
        print(f"Pipeline failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
