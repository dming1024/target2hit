"""Report generation: JSON and HTML."""
from __future__ import annotations
import json
import logging
from pathlib import Path
from dataclasses import asdict
from workflow.contracts import PipelineContext, ReportResult

logger = logging.getLogger(__name__)


def generate_report(ctx: PipelineContext, output_dir: Path) -> ReportResult:
    """Generate pipeline report in JSON and HTML formats."""
    output_dir.mkdir(parents=True, exist_ok=True)
    job_id = ctx.job_id

    report_data = _build_report_data(ctx)

    # JSON report
    json_path = output_dir / f"report_{job_id}.json"
    json_path.write_text(json.dumps(report_data, indent=2, default=str))

    # HTML report
    html_path = output_dir / f"report_{job_id}.html"
    html_content = _render_html(report_data)
    html_path.write_text(html_content)

    return ReportResult(report_json=json_path, report_html=html_path)


def _build_report_data(ctx: PipelineContext) -> dict:
    data = {"job_id": ctx.job_id, "gene_symbol": ctx.gene_symbol, "disease": ctx.disease}
    for module_name, output in ctx.previous.items():
        try:
            data[module_name] = asdict(output)
        except (TypeError, AttributeError):
            data[module_name] = str(output)
    return data


def _render_html(data: dict) -> str:
    from jinja2 import Template
    template_path = Path(__file__).parent / "templates" / "report.html"
    if template_path.exists():
        template = Template(template_path.read_text())
        return template.render(**data)

    # Fallback simple HTML
    ranking = data.get("ranking", {})
    hits_html = ""
    for hit in ranking.get("hits", [])[:20]:
        hits_html += f"<tr><td>{hit['rank']}</td><td>{hit['compound_id']}</td><td>{hit['smiles'][:50]}</td><td>{hit['final_score']:.4f}</td></tr>"

    return f"""<!DOCTYPE html>
<html><head><title>Target2Hit Report - {data['gene_symbol']}</title>
<style>body{{font-family:-apple-system,sans-serif;max-width:960px;margin:0 auto;padding:20px}}table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}th{{background:#f5f5f5}}</style></head>
<body><h1>Target-to-Hit Discovery Report</h1>
<h2>Gene: {data['gene_symbol']} | Disease: {data.get('disease', 'N/A')} | Job: {data['job_id']}</h2>
<h3>Top Hits</h3>
<table><tr><th>Rank</th><th>ID</th><th>SMILES</th><th>Score</th></tr>{hits_html}</table></body></html>"""
