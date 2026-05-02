from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class CompareMembers(Pattern):
    name = "compare_members"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        role_a = params["member_a"]
        role_b = params["member_b"]
        path = params["field"]
        comparison = params["comparison"]
        threshold = float(params["threshold"])
        in_year = params.get("in_year")
        in_range = params.get("in_year_range")
        only_in = params.get("only_in_years_where")

        a = next((m for m in household["members"] if m["role"] == role_a), None)
        b = next((m for m in household["members"] if m["role"] == role_b), None)
        if not a or not b:
            return PatternResult(False)

        rows_a = {r["tax_year"]: r["value"] for r in facts.fields_by_year(a, household, path)}
        rows_b = {r["tax_year"]: r["value"] for r in facts.fields_by_year(b, household, path)}

        years = sorted(set(rows_a.keys()) & set(rows_b.keys()))
        if in_year is not None:
            years = [y for y in years if y == in_year]
        if in_range:
            lo, hi = in_range
            years = [y for y in years if lo <= y <= hi]

        # only_in_years_where: v0 partial implementation — used as a household-level guard.
        # Per-year filtering of nested logic is deferred; if either member satisfies the
        # nested logic, comparisons across all otherwise-matching years are allowed.
        if only_in:
            from app.engine.runner import _eval_logic

            ok_a, _ = _eval_logic(only_in, a, household)
            ok_b, _ = _eval_logic(only_in, b, household)
            if not (ok_a or ok_b):
                return PatternResult(False)

        for y in years:
            try:
                va = float(rows_a[y])
                vb = float(rows_b[y])
            except (TypeError, ValueError):
                continue
            diff = va - vb
            ok = False
            if comparison == "absolute_difference_gt":
                ok = abs(diff) > threshold
            elif comparison == "ratio_gt":
                ok = vb != 0 and (va / vb) > threshold
            elif comparison == "ratio_lt":
                ok = vb != 0 and (va / vb) < threshold
            elif comparison == "a_gt_b":
                ok = (va - vb) > threshold
            elif comparison == "a_lt_b":
                ok = (vb - va) > threshold
            if ok:
                return PatternResult(
                    True,
                    {
                        "matching_year": y,
                        "value_a": va,
                        "value_b": vb,
                        "difference_value": diff,
                    },
                )
        return PatternResult(False)
