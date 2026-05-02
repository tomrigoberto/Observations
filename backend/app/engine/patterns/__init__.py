from app.engine.patterns.age_in_year import AgeInYear
from app.engine.patterns.aggregate_threshold import AggregateThreshold
from app.engine.patterns.compare_members import CompareMembers
from app.engine.patterns.count_threshold import CountThreshold
from app.engine.patterns.custom_expression import CustomExpression
from app.engine.patterns.field_change_year_over_year import FieldChangeYearOverYear
from app.engine.patterns.field_compare import FieldCompare
from app.engine.patterns.filing_status_equals import FilingStatusEquals
from app.engine.patterns.filing_status_transition import FilingStatusTransition
from app.engine.patterns.form_absent import FormAbsent
from app.engine.patterns.form_present import FormPresent
from app.engine.patterns.member_relationship import MemberRelationship
from app.engine.patterns.presence_of_entity import PresenceOfEntity
from app.engine.patterns.transaction_code_absent import TransactionCodeAbsent
from app.engine.patterns.transaction_code_present import TransactionCodePresent
from app.engine.patterns.transaction_code_sequence import TransactionCodeSequence
from app.engine.patterns.unfiled_year import UnfiledYear
from app.engine.patterns.years_of_data_present import YearsOfDataPresent

_REGISTRY = {
    p.name: p
    for p in [
        FilingStatusTransition(),
        FilingStatusEquals(),
        TransactionCodePresent(),
        TransactionCodeAbsent(),
        TransactionCodeSequence(),
        FormPresent(),
        FormAbsent(),
        FieldCompare(),
        FieldChangeYearOverYear(),
        AggregateThreshold(),
        CountThreshold(),
        AgeInYear(),
        YearsOfDataPresent(),
        UnfiledYear(),
        MemberRelationship(),
        CompareMembers(),
        PresenceOfEntity(),
        CustomExpression(),
    ]
}


def get(name: str):
    return _REGISTRY.get(name)


def all_names() -> list[str]:
    return sorted(_REGISTRY.keys())
