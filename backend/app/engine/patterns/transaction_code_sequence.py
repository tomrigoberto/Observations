from datetime import date

from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class TransactionCodeSequence(Pattern):
    name = "transaction_code_sequence"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        first_spec = params["first"]
        then_spec = params["then"]
        same_tax_year = params.get("same_tax_year", False)
        within_days = params.get("within_days")
        in_range = params.get("in_year_range")

        events_with_dates: list[tuple[date, dict]] = []
        for e in facts.tc_events(member, household):
            d = e.get("date")
            try:
                parsed = date.fromisoformat(d) if isinstance(d, str) else None
            except ValueError:
                parsed = None
            if parsed is None:
                continue
            events_with_dates.append((parsed, e))
        events_with_dates.sort(key=lambda x: x[0])

        for i, (d1, e1) in enumerate(events_with_dates):
            if not _matches_spec(e1, first_spec):
                continue
            if in_range and (
                e1.get("tax_year") is None
                or not (in_range[0] <= e1["tax_year"] <= in_range[1])
            ):
                continue
            for d2, e2 in events_with_dates[i + 1 :]:
                if not _matches_spec(e2, then_spec):
                    continue
                if same_tax_year and e1.get("tax_year") != e2.get("tax_year"):
                    continue
                days = (d2 - d1).days
                if within_days is not None and days > within_days:
                    continue
                return PatternResult(
                    fired=True,
                    captures={
                        "first_event_date": d1.isoformat(),
                        "then_event_date": d2.isoformat(),
                        "tax_year": e1.get("tax_year"),
                        "days_between_events": days,
                    },
                )
        return PatternResult(fired=False)


def _matches_spec(e: dict, spec: dict) -> bool:
    if e.get("code") != spec["code"]:
        return False
    if spec.get("action_code_any_of"):
        if e.get("action_code") not in set(spec["action_code_any_of"]):
            return False
    return True
