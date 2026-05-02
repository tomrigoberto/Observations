"""Tiny safe templating for {{...}} placeholders inside observation statements.

No conditionals, no loops. Allowed:
  - dotted attribute access on the context (``member.display_name``)
  - referencing captured variable names (``transition_year``)
  - simple integer arithmetic (``transition_year - 1``)
  - calls to a small set of formatters (``currency(amount)``, ``percent(rate)``,
    ``date(d)``)
"""

from __future__ import annotations

import re
from datetime import date, datetime

_PLACEHOLDER_RE = re.compile(r"{{\s*(?P<expr>[^{}]+?)\s*}}")
_INT_OP_RE = re.compile(r"^(?P<base>[A-Za-z_][A-Za-z0-9_.]*)\s*(?P<op>[+\-])\s*(?P<n>\d+)$")
_FUNC_RE = re.compile(r"^(?P<fn>[a-z_]+)\((?P<arg>[A-Za-z_][A-Za-z0-9_.]*)\)$")


def render(template: str, context: dict) -> str:
    def sub(match: re.Match) -> str:
        expr = match.group("expr").strip()
        return str(_evaluate(expr, context))

    return _PLACEHOLDER_RE.sub(sub, template)


def _evaluate(expr: str, ctx: dict):
    if m := _FUNC_RE.match(expr):
        return _formatters[m.group("fn")](_lookup(m.group("arg"), ctx))
    if m := _INT_OP_RE.match(expr):
        base = _lookup(m.group("base"), ctx)
        n = int(m.group("n"))
        return int(base) + n if m.group("op") == "+" else int(base) - n
    return _lookup(expr, ctx)


def _lookup(path: str, ctx: dict):
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
        if cur is None:
            return f"{{{{missing:{path}}}}}"
    return cur


def _currency(value) -> str:
    if value is None:
        return "$0"
    try:
        return f"${float(value):,.0f}"
    except (TypeError, ValueError):
        return str(value)


def _percent(value) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return str(value)


def _date(value) -> str:
    if isinstance(value, (date, datetime)):
        return value.strftime("%b %d, %Y")
    return str(value)


_formatters = {
    "currency": _currency,
    "percent": _percent,
    "date": _date,
}
