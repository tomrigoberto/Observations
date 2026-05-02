import logging

from app.engine.dsl import DSLError, build_env, safe_eval
from app.engine.patterns.base import Pattern, PatternResult

log = logging.getLogger(__name__)


class CustomExpression(Pattern):
    """Escape hatch pattern that evaluates a sandboxed DSL expression.

    Parameters:
        expression (str, required): Boolean DSL expression. Fires when truthy.
        captures   (dict[str, str], optional): name → DSL expression. Each is evaluated
            after the boolean expression succeeds; the values are exposed as captures
            for the observation's statement and sources.

    Use sparingly. Authors using this pattern must set
    ``metadata.legal_review_required: true`` and obtain a tax-lead reviewer.
    """

    name = "custom_expression"

    def evaluate(self, member: dict, household: dict, params: dict) -> PatternResult:
        expr = params.get("expression")
        if not expr:
            return PatternResult(False)
        env = build_env(member, household)
        try:
            ok = bool(safe_eval(expr, env))
        except DSLError as e:
            log.warning("DSL error in custom_expression: %s", e)
            return PatternResult(False)
        if not ok:
            return PatternResult(False)

        captures: dict = {}
        for name, sub_expr in (params.get("captures") or {}).items():
            try:
                captures[name] = safe_eval(sub_expr, env)
            except DSLError as e:
                log.warning("DSL error in capture %s: %s", name, e)
                captures[name] = None
        return PatternResult(True, captures)
