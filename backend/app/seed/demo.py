"""One-shot demo seeder.

Creates a 'Smith Family (demo)' client with synthetic, pre-parsed transcripts
that exercise several of the example observations in the library starter:

  - Filing-status transition Single → MFJ in 2022    (OBS-LIFE-0042)
  - Examination indicator (TC 420) on 2021 return     (OBS-TAX-0010, OBS-TAX-0070)
  - Wage gap between spouses in 2022                  (OBS-FIN-0001)
  - RMD age in 2024 (primary born 1950)               (OBS-TAX-0030)

Run via the Makefile:
    make seed-demo

Idempotent: re-running prints 'already seeded' and exits cleanly.
"""

from __future__ import annotations

from app import models
from app.db import SessionLocal, init_db

DEMO_CLIENT_NAME = "Smith Family (demo)"


def main() -> int:
    init_db()
    db = SessionLocal()
    try:
        if db.query(models.Client).filter(models.Client.name == DEMO_CLIENT_NAME).first():
            print(f"already seeded: {DEMO_CLIENT_NAME!r}")
            return 0

        client = models.Client(name=DEMO_CLIENT_NAME)
        db.add(client)
        db.flush()

        primary = models.Member(
            client_id=client.id,
            role="primary_taxpayer",
            display_name="Alex Smith",
            birth_year=1950,  # age 74 in 2024 — triggers RMD observation
        )
        spouse = models.Member(
            client_id=client.id,
            role="spouse",
            display_name="Jordan Smith",
            birth_year=1952,
        )
        db.add_all([primary, spouse])
        db.flush()

        primary_transcripts = [
            (
                "account_transcript",
                2020,
                {
                    "header": {
                        "filing_status": "Single",
                        "agi": 95000,
                        "wages_total": 92000,
                    },
                    "tc_events": [
                        {"code": 150, "date": "2021-04-15", "amount": 0, "tax_year": 2020}
                    ],
                },
            ),
            (
                "account_transcript",
                2021,
                {
                    "header": {
                        "filing_status": "Single",
                        "agi": 105000,
                        "wages_total": 102000,
                    },
                    "tc_events": [
                        {"code": 150, "date": "2022-04-15", "amount": 0, "tax_year": 2021},
                        {"code": 420, "date": "2023-06-20", "amount": 0, "tax_year": 2021},
                    ],
                },
            ),
            (
                "account_transcript",
                2022,
                {
                    "header": {
                        "filing_status": "Married_Filing_Jointly",
                        "agi": 245000,
                        "wages_total": 215000,
                    },
                    "tc_events": [
                        {"code": 150, "date": "2023-04-15", "amount": 0, "tax_year": 2022}
                    ],
                },
            ),
        ]
        for ttype, year, data in primary_transcripts:
            db.add(
                models.Transcript(
                    client_id=client.id,
                    member_id=primary.id,
                    transcript_type=ttype,
                    tax_year=year,
                    source_filename=f"demo_{ttype}_{year}_primary.html",
                    raw_html_path="(demo seed; no raw file)",
                    parse_status="parsed",
                    parsed_data=data,
                )
            )

        db.add(
            models.Transcript(
                client_id=client.id,
                member_id=spouse.id,
                transcript_type="account_transcript",
                tax_year=2022,
                source_filename="demo_account_transcript_2022_spouse.html",
                raw_html_path="(demo seed; no raw file)",
                parse_status="parsed",
                parsed_data={
                    "header": {
                        "filing_status": "Married_Filing_Jointly",
                        "wages_total": 35000,
                        "agi": 245000,
                    },
                    "tc_events": [
                        {"code": 150, "date": "2023-04-15", "amount": 0, "tax_year": 2022}
                    ],
                },
            )
        )

        db.commit()
        print(
            f"seeded {DEMO_CLIENT_NAME!r} (client_id={client.id}) with "
            f"{len(primary_transcripts) + 1} transcripts."
        )
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
