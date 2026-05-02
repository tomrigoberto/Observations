from app.engine.patterns.base import Pattern, PatternResult


class MemberRelationship(Pattern):
    name = "member_relationship"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        roles = set(params.get("role_any_of", []))
        role = member.get("role")
        if role in roles:
            return PatternResult(True, {"member_role": role})
        return PatternResult(False)
