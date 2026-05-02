from app.parsers.account_transcript import parse as parse_account
from app.parsers.wage_and_income import parse as parse_wage_and_income

_PARSERS = {
    "account_transcript": parse_account,
    "wage_and_income": parse_wage_and_income,
}


def parse_transcript(transcript_type: str, html: str) -> dict:
    parser = _PARSERS.get(transcript_type)
    if not parser:
        raise ValueError(f"no parser for transcript_type={transcript_type}")
    return parser(html)
