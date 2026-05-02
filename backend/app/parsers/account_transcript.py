"""Parser for IRS Account Transcript HTML.

This is a v0 parser. It is intentionally minimal and tolerant: it tries
several common HTML structures (table rows, definition lists, plain text)
and normalizes filing status into our canonical enum.

For production we will need golden tests against several real HTML
transcript layouts, plus regression tests for IRS format changes.
"""

import re

from app.parsers.base import normalize_filing_status, soupify

_TC_LINE_RE = re.compile(
    r"^(?P<code>\d{3})\s+(?P<desc>[A-Za-z][A-Za-z0-9 \-/&]+?)\s+(?P<date>\d{2}-\d{2}-\d{4})"
    r"(?:\s+(?P<amount>-?\$?[\d,]+\.\d{2}))?"
)

_FILING_STATUS_RE = re.compile(r"FILING STATUS\s*:?\s*(.+)", re.IGNORECASE)
_TAX_PERIOD_RE = re.compile(r"TAX PERIOD\s*:?\s*(?:DEC )?(\d{4})", re.IGNORECASE)


def parse(html: str) -> dict:
    soup = soupify(html)
    text = soup.get_text("\n")

    filing_status = None
    tax_year = None
    if m := _FILING_STATUS_RE.search(text):
        filing_status = normalize_filing_status(m.group(1).split("\n")[0])
    if m := _TAX_PERIOD_RE.search(text):
        tax_year = int(m.group(1))

    tc_events = []
    for line in text.splitlines():
        line = line.strip()
        if m := _TC_LINE_RE.match(line):
            amount_str = m.group("amount") or ""
            amount = (
                float(amount_str.replace(",", "").replace("$", "")) if amount_str else None
            )
            tc_events.append(
                {
                    "code": int(m.group("code")),
                    "description": m.group("desc").strip(),
                    "date": _normalize_date(m.group("date")),
                    "amount": amount,
                    "tax_year": tax_year,
                }
            )

    return {
        "header": {"filing_status": filing_status, "tax_year": tax_year},
        "tc_events": tc_events,
    }


def _normalize_date(s: str) -> str:
    mm, dd, yyyy = s.split("-")
    return f"{yyyy}-{mm}-{dd}"
