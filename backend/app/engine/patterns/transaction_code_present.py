from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class TransactionCodePresent(Pattern):
    name = "transaction_code_present"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        code = params["code"]
        in_year = params.get("in_year")
        year_range = params.get("in_year_range")
        action_codes = set(params.get("action_code_any_of", []) or [])
        amount_gt = params.get("amount_gt")
        amount_lt = params.get("amount_lt")
        amount_between = params.get("amount_between")

        events = facts.tc_events(member, household, code=code)
        for e in events:
            year = e.get("tax_year")
            if in_year is not None and year != in_year:
                continue
            if year_range and (year is None or year < year_range[0] or year > year_range[1]):
                continue
            if action_codes and e.get("action_code") not in action_codes:
                continue
            amount = e.get("amount")
            if amount_gt is not None and (amount is None or amount <= amount_gt):
                continue
            if amount_lt is not None and (amount is None or amount >= amount_lt):
                continue
            if amount_between and (
                amount is None or amount < amount_between[0] or amount > amount_between[1]
            ):
                continue
            return PatternResult(
                fired=True,
                captures={
                    "event_year": year,
                    "event_date": e.get("date"),
                    "event_amount": amount,
                    "event_action_code": e.get("action_code"),
                },
            )
        return PatternResult(fired=False)
