from __future__ import annotations

from datetime import datetime, timedelta


class PatentQueryBuilder:
    """Build optimized BigQuery SQL queries for cybersecurity patents."""

    CYBERSECURITY_CPC_CODES = [
        "H04L%",     # Digital transmission / cryptography
        "G06F21%",   # Computer security
        "H04W12%",   # Wireless security
        "H04L9%",    # Cryptography mechanisms
    ]

    def __init__(self, lookback_days: int = 7, countries: list[str] | None = None):
        self.lookback_days = lookback_days
        self.countries = countries or ["US"]

    def get_date_range(self) -> tuple[str, str]:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=self.lookback_days)
        return (start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d"))

    def build_patent_query(self, start_date: str, end_date: str) -> str:
        countries_filter = ",".join([f"'{c}'" for c in self.countries])
        cpc_like_clauses = " OR ".join([f"c.code LIKE '{like}'" for like in self.CYBERSECURITY_CPC_CODES])

        # Note: Using SAFE_OFFSET for localized arrays to avoid errors when empty
        query = f"""
        SELECT 
            publication_number,
            title_localized[SAFE_OFFSET(0)].text AS title,
            abstract_localized[SAFE_OFFSET(0)].text AS abstract,
            filing_date,
            publication_date,
            country_code,
            kind_code,
            ARRAY_AGG(DISTINCT assignee.name IGNORE NULLS) AS assignees,
            ARRAY_AGG(DISTINCT inventor.name IGNORE NULLS) AS inventors,
            ARRAY_AGG(DISTINCT cpc.code IGNORE NULLS) AS cpc_codes
        FROM 
            `patents-public-data.patents.publications`
        WHERE
            filing_date BETWEEN {start_date} AND {end_date}
            AND country_code IN ({countries_filter})
            AND EXISTS (
                SELECT 1 FROM UNNEST(cpc) AS c
                WHERE {cpc_like_clauses}
            )
        GROUP BY
            publication_number, title, abstract, filing_date, publication_date, country_code, kind_code
        ORDER BY publication_date DESC
        LIMIT 1000
        """
        return query


