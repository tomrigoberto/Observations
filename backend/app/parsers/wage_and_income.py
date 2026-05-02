"""Parser for IRS Wage & Income Transcript HTML (v0 — stub).

Returns a normalized list of information returns. The shape:

[
  {
    "form_type": "W-2" | "1099-R" | "1099-INT" | ...,
    "tax_year": int,
    "payer": str,
    "box_1": float,
    "taxable_amount": float,
    "distribution_code": str | None,
    "raw": dict   # raw fields preserved for source citations
  }
]

Production parsing requires golden tests against several real layouts.
"""

from app.parsers.base import soupify


def parse(html: str) -> dict:
    soup = soupify(html)
    # placeholder — a real implementation walks form sections in order
    return {"forms": [], "raw_text_sample": soup.get_text(" ")[:2000]}
