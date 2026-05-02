from app.engine.patterns.filing_status_transition import FilingStatusTransition
from app.engine.patterns.transaction_code_present import TransactionCodePresent
from app.engine.patterns.form_present import FormPresent
from app.engine.patterns.unimplemented import UnimplementedPattern

_REGISTRY = {
    p.name: p
    for p in [
        FilingStatusTransition(),
        TransactionCodePresent(),
        FormPresent(),
    ]
}

# Patterns documented in the catalog but not yet implemented in v0 fall back
# to a permissive stub that always returns False with a structured warning.
_STUBBED = [
    "filing_status_equals",
    "transaction_code_absent",
    "transaction_code_sequence",
    "form_absent",
    "field_compare",
    "field_change_year_over_year",
    "aggregate_threshold",
    "count_threshold",
    "age_in_year",
    "years_of_data_present",
    "unfiled_year",
    "member_relationship",
    "compare_members",
    "presence_of_entity",
    "custom_expression",
]
for _name in _STUBBED:
    _REGISTRY[_name] = UnimplementedPattern(_name)


def get(name: str):
    return _REGISTRY.get(name)


def all_names() -> list[str]:
    return sorted(_REGISTRY.keys())
