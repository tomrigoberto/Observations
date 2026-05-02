from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PatternResult:
    fired: bool
    captures: dict = field(default_factory=dict)


class Pattern:
    name: str = ""

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        raise NotImplementedError
