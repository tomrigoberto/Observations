from bs4 import BeautifulSoup


def soupify(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "lxml")


FILING_STATUS_NORMALIZE = {
    "single": "Single",
    "married filing jointly": "Married_Filing_Jointly",
    "married filing joint": "Married_Filing_Jointly",
    "married filing separately": "Married_Filing_Separately",
    "married filing separate": "Married_Filing_Separately",
    "head of household": "Head_of_Household",
    "qualifying surviving spouse": "Qualifying_Surviving_Spouse",
    "qualifying widow(er)": "Qualifying_Surviving_Spouse",
}


def normalize_filing_status(raw: str | None) -> str | None:
    if not raw:
        return None
    return FILING_STATUS_NORMALIZE.get(raw.strip().lower())
