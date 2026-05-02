from app.engine import facts
from app.engine.patterns.base import Pattern, PatternResult


class YearsOfDataPresent(Pattern):
    name = "years_of_data_present"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        transcript_type = params["transcript_type"]
        min_years = int(params["min_years"])
        years = facts.tax_years_present(member, household, transcript_type)
        if len(years) >= min_years:
            return PatternResult(
                True,
                {"years_present": years, "years_present_count": len(years)},
            )
        return PatternResult(False)
