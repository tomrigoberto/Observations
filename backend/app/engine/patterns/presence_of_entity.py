from app.engine.patterns.base import Pattern, PatternResult

# Allow analysts to write either canonical scope names ("business_entity") or
# the bare entity types stored on the household ("business").
_TYPE_ALIASES = {"business_entity": "business"}


class PresenceOfEntity(Pattern):
    name = "presence_of_entity"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        types = set(params.get("entity_type_any_of", []))
        normalized = {_TYPE_ALIASES.get(t, t) for t in types}
        for e in household.get("entities", []) or []:
            t = e.get("type")
            if t in normalized or t in types:
                return PatternResult(
                    True,
                    {
                        "entity_id": e.get("id"),
                        "entity_type": t,
                        "entity_name": e.get("name"),
                    },
                )
        return PatternResult(False)
