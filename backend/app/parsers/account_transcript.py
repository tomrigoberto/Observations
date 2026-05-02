"""Parser for IRS Account Transcript HTML.

v0 parser: minimal but useful. Extracts:
  - filing status
  - tax year
  - common labeled numeric fields (AGI, taxable income, account balance, ...)
  - transaction-code events

Production parsing requires golden tests against multiple real layouts.
"""

import re

from app.parsers.base import normalize_filing_status, soupify

_TC_LINE_RE = re.compile(
    r"^(?P<code>\d{3})\s+(?P<desc>[A-Za-z][A-Za-z0-9 \-/&]+?)\s+(?P<date>\d{2}-\d{2}-\d{4})"
    r"(?:\s+(?P<amount>-?\$?[\d,]+\.\d{2}))?"
)
_FILING_STATUS_RE = re.compile(r"FILING STATUS\s*:?\s*(.+)", re.IGNORECASE)
_TAX_PERIOD_RE = re.compile(r"TAX PERIOD\s*:?\s*(?:DEC )?(\d{4})", re.IGNORECASE)
_NUMERIC_VALUE = r"\$?(-?[\d,]+(?:\.\d{2})?)"

# Common numeric labels on Account Transcripts.
_NUMERIC_FIELDS: list[tuple[str, str]] = [
    ("agi", r"ADJUSTED GROSS INCOME"),
    ("taxable_income", r"TAXABLE INCOME"),
    ("tax_per_return", r"TAX PER RETURN"),
    ("account_balance", r"ACCOUNT BALANCE"),
    ("accrued_interest", r"ACCRUED INTEREST"),
    ("accrued_penalty", r"ACCRUED PENALTY"),
    ("total_credits", r"TOTAL CREDITS"),
    ("se_taxable_income", r"SE TAXABLE INCOME TAXPAYER"),
]


def parse(html: str) -> dict:
    soup = soupify(html)
    text = soup.get_text("\n")

    filing_status = None
    tax_year = None
    if m := _FILING_STATUS_RE.search(text):
        filing_status = normalize_filing_status(m.group(1).split("\n")[0])
    if m := _TAX_PERIOD_RE.search(text):
        tax_year = int(m.group(1))

    amounts: dict[str, float] = {}
    for field_name, label in _NUMERIC_FIELDS:
        v = _extract_numeric(text, label)
        if v is not None:
            amounts[field_name] = v

    tc_events = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
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
        "header": {"filing_status": filing_status, "tax_year": tax_year, **amounts},
        "tc_events": tc_events,
    }


def _normalize_date(s: str) -> str:
    mm, dd, yyyy = s.split("-")
    return f"{yyyy}-{mm}-{dd}"


def _extract_numeric(text: str, label: str) -> float | None:
    m = re.search(rf"{label}\s*:?\s*{_NUMERIC_VALUE}", text, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except (TypeError, ValueError):
        return None
