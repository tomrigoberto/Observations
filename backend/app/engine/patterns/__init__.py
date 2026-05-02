from app.engine.patterns.age_in_year import AgeInYear
from app.engine.patterns.field_compare import FieldCompare
from app.engine.patterns.filing_status_equals import FilingStatusEquals
from app.engine.patterns.filing_status_transition import FilingStatusTransition
from app.engine.patterns.form_present import FormPresent
from app.engine.patterns.transaction_code_absent import TransactionCodeAbsent
from app.engine.patterns.transaction_code_present import TransactionCodePresent
from app.engine.patterns.unimplemented import UnimplementedPattern
from app.engine.patterns.years_of_data_present import YearsOfDataPresent

_REGISTRY = {
    p.name: p
    for p in [
        FilingStatusTransition(),
        FilingStatusEquals(),
        TransactionCodePresent(),
        TransactionCodeAbsent(),
        FormPresent(),
        YearsOfDataPresent(),
        FieldCompare(),
        AgeInYear(),
    ]
}

# Patterns documented in the catalog but not yet implemented in v0 fall back
# to a permissive stub that always returns False.
_STUBBED = [
    "transaction_code_sequence",
    "form_absent",
    "field_change_year_over_year",
    "aggregate_threshold",
    "count_threshold",
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
