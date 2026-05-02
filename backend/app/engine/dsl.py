"""Sandboxed evaluator for the DSL escape hatch.

The DSL is intentionally a tiny subset of Python expression syntax — we parse
with :mod:`ast` and reject any node type not on the allowlist before evaluating.
This gives us a familiar surface for authors who happen to know Python, without
running unsanctioned code paths.

Allowed:
  - literals (numbers, strings, lists, tuples, ``None``)
  - boolean ops (``and``, ``or``, ``not``)
  - arithmetic on numbers (``+ - * / // %``)
  - comparisons (``== != < <= > >= in not in``)
  - attribute access on dicts (treated as key access) and namedtuples
  - subscript by index/key
  - lambdas with exactly one positional argument
  - calls to functions in the prepared environment
  - if-expressions

Disallowed (rejected at parse time): assignments, statements, comprehensions,
imports, attribute access on private attrs, ``__dunder__`` names, ``exec``/``eval``,
class/function definitions, generators, await/async, walrus.
"""

from __future__ import annotations

import ast
from datetime import date

from app.engine import facts as F


class DSLError(Exception):
    pass


_ALLOWED = (
    ast.Expression,
    ast.BoolOp,
    ast.BinOp,
    ast.UnaryOp,
    ast.Compare,
    ast.Call,
    ast.Name,
    ast.Constant,
    ast.Attribute,
    ast.Subscript,
    ast.List,
    ast.Tuple,
    ast.IfExp,
    ast.Lambda,
    ast.arguments,
    ast.arg,
    ast.And,
    ast.Or,
    ast.Not,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.USub,
    ast.UAdd,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Load,
    ast.keyword,
)


def safe_eval(expr: str, env: dict):
    try:
        tree = ast.parse(expr.strip(), mode="eval")
    except SyntaxError as e:
        raise DSLError(f"syntax error: {e}") from None
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED):
            raise DSLError(f"disallowed expression: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id.startswith("_"):
            raise DSLError(f"private name not allowed: {node.id}")
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            raise DSLError(f"private attribute not allowed: {node.attr}")
    return _eval(tree.body, env)


def _eval(node, env):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in env:
            return env[node.id]
        raise DSLError(f"unknown name: {node.id}")
    if isinstance(node, ast.Attribute):
        obj = _eval(node.value, env)
        if isinstance(obj, dict):
            if node.attr in obj:
                return obj[node.attr]
            raise DSLError(f"no key {node.attr!r}")
        return getattr(obj, node.attr)
    if isinstance(node, ast.Subscript):
        obj = _eval(node.value, env)
        idx = _eval(node.slice, env)
        return obj[idx]
    if isinstance(node, ast.UnaryOp):
        v = _eval(node.operand, env)
        if isinstance(node.op, ast.Not):
            return not v
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return +v
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            r = True
            for v in node.values:
                r = _eval(v, env)
                if not r:
                    return r
            return r
        if isinstance(node.op, ast.Or):
            for v in node.values:
                r = _eval(v, env)
                if r:
                    return r
            return False
    if isinstance(node, ast.BinOp):
        a = _eval(node.left, env)
        b = _eval(node.right, env)
        if isinstance(node.op, ast.Add):
            return a + b
        if isinstance(node.op, ast.Sub):
            return a - b
        if isinstance(node.op, ast.Mult):
            return a * b
        if isinstance(node.op, ast.Div):
            return a / b
        if isinstance(node.op, ast.FloorDiv):
            return a // b
        if isinstance(node.op, ast.Mod):
            return a % b
    if isinstance(node, ast.Compare):
        left = _eval(node.left, env)
        ok = True
        for op, comp in zip(node.ops, node.comparators):
            right = _eval(comp, env)
            if isinstance(op, ast.Eq):
                ok = ok and (left == right)
            elif isinstance(op, ast.NotEq):
                ok = ok and (left != right)
            elif isinstance(op, ast.Lt):
                ok = ok and (left < right)
            elif isinstance(op, ast.LtE):
                ok = ok and (left <= right)
            elif isinstance(op, ast.Gt):
                ok = ok and (left > right)
            elif isinstance(op, ast.GtE):
                ok = ok and (left >= right)
            elif isinstance(op, ast.In):
                ok = ok and (left in right)
            elif isinstance(op, ast.NotIn):
                ok = ok and (left not in right)
            left = right
        return ok
    if isinstance(node, ast.IfExp):
        return _eval(node.body, env) if _eval(node.test, env) else _eval(node.orelse, env)
    if isinstance(node, ast.List):
        return [_eval(x, env) for x in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_eval(x, env) for x in node.elts)
    if isinstance(node, ast.Lambda):
        if len(node.args.args) != 1 or node.args.vararg or node.args.kwarg:
            raise DSLError("lambda must take exactly one positional argument")
        param_name = node.args.args[0].arg
        body = node.body
        captured = env

        def _l(x, _b=body, _e=captured, _p=param_name):
            return _eval(_b, {**_e, _p: x})

        return _l
    if isinstance(node, ast.Call):
        fn = _eval(node.func, env)
        args = [_eval(a, env) for a in node.args]
        kwargs = {kw.arg: _eval(kw.value, env) for kw in node.keywords}
        return fn(*args, **kwargs)
    raise DSLError(f"unsupported: {type(node).__name__}")


def build_env(member: dict, household: dict) -> dict:
    """Construct the evaluation environment for a single observation evaluation."""

    def has_transition(series, from_in=None, to_in=None, consecutive=True):
        from_set = set(from_in or [])
        to_set = set(to_in or [])
        for i in range(1, len(series)):
            prev, curr = series[i - 1], series[i]
            if prev["status"] in from_set and curr["status"] in to_set:
                if consecutive and curr["tax_year"] - prev["tax_year"] != 1:
                    continue
                return True
        return False

    def first_transition_year(series, from_in=None, to_in=None):
        from_set = set(from_in or [])
        to_set = set(to_in or [])
        for i in range(1, len(series)):
            prev, curr = series[i - 1], series[i]
            if prev["status"] in from_set and curr["status"] in to_set:
                return curr["tax_year"]
        return None

    def status_at(series, year=None):
        for r in series:
            if r["tax_year"] == year:
                return r["status"]
        return None

    def status_before(series, year=None):
        before = [r for r in series if r["tax_year"] < year]
        return before[-1]["status"] if before else None

    def days_between(a, b):
        if isinstance(a, str):
            a = date.fromisoformat(a)
        if isinstance(b, str):
            b = date.fromisoformat(b)
        return (b - a).days

    def years_between(a, b):
        return abs(b - a)

    def _any(lst, where=None):
        if where is None:
            return any(lst)
        return any(where(x) for x in lst)

    def _count(lst, where=None):
        if where is None:
            return len(list(lst))
        return sum(1 for x in lst if where(x))

    def _sum(lst, of=None):
        if of is None:
            return sum(lst)
        return sum(of(x) for x in lst)

    facts_ns = {
        "filing_status_by_year": lambda m: F.filing_status_by_year(m, household),
        "tc_events": lambda m, code=None, year=None: F.tc_events(
            m, household, code=code, year=year
        ),
        "forms": lambda m, type=None, year=None: F.forms(  # noqa: A002
            m, household, form_type=type, year=year
        ),
        "field": lambda m, year, path: F.field(m, household, path, year),
        "tax_years_present": lambda m, transcript_type=None: F.tax_years_present(
            m, household, transcript_type
        ),
    }

    return {
        "member": member,
        "facts": facts_ns,
        "has_transition": has_transition,
        "first_transition_year": first_transition_year,
        "status_at": status_at,
        "status_before": status_before,
        "days_between": days_between,
        "years_between": years_between,
        "any": _any,
        "count": _count,
        "sum": _sum,
        "max": lambda lst: max(lst) if lst else None,
        "min": lambda lst: min(lst) if lst else None,
        "between": lambda v, low, high: low <= v <= high,
        "abs": abs,
        "null": None,
    }
