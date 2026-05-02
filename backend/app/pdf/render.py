"""PDF rendering for the executive summary and the detailed report.

Uses Jinja2 to render an HTML template, then WeasyPrint to convert HTML to PDF.
This is a v0 stub; the templates render minimally but correctly.
"""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

TEMPLATE_DIR = Path(__file__).parent / "templates"
_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_exec_summary(context: dict) -> bytes:
    html = _env.get_template("exec_summary.html").render(**context)
    return HTML(string=html).write_pdf()


def render_detail_report(context: dict) -> bytes:
    html = _env.get_template("detail_report.html").render(**context)
    return HTML(string=html).write_pdf()
