"""Placeholder exports: PDF/Excel generation helpers.

These are minimal implementations; replace with real exporters like pandas/openpyxl or reportlab.
"""
import os
from pathlib import Path


async def export_requests_placeholder() -> str:
    """Create a small placeholder file and return path to it."""
    out = Path(os.path.dirname(__file__)) / ".." / "data" / "export"
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    path = out / "requests_export.txt"
    path.write_text("This is a placeholder export. Implement real export functionality.")
    return str(path)
