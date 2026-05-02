from app.engine.patterns.base import Pattern, PatternResult


class UnimplementedPattern(Pattern):
    """v0 stub for patterns documented in the catalog but not yet implemented.

    The runner logs a warning and treats the pattern as not firing. This lets
    analysts author observations against the documented catalog without having
    every pattern implemented yet — the rule simply won't fire until engineering
    ships the pattern.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        return PatternResult(fired=False, captures={"_unimplemented": self.name})
