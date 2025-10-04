from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from typing import List, Optional, Dict, Any


def _parse_yyyymmdd(value: Any) -> Optional[date]:
    """Parse INT or string formatted as YYYYMMDD into a date.

    Returns None if the value is falsy or invalid.
    """
    if value in (None, ""):
        return None
    try:
        # BigQuery often returns INT like 20240101
        if isinstance(value, int):
            s = str(value)
        else:
            s = str(value).strip()
        return datetime.strptime(s, "%Y%m%d").date()
    except Exception:
        return None


@dataclass
class Patent:
    publication_number: str
    title: str
    abstract: str
    filing_date: Optional[date]
    publication_date: Optional[date]
    assignees: List[str] = field(default_factory=list)
    inventors: List[str] = field(default_factory=list)
    cpc_codes: List[str] = field(default_factory=list)
    country: Optional[str] = None
    kind_code: Optional[str] = None

    # Computed/derived fields
    is_cybersecurity: bool = False
    relevance_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to a serializable dictionary for persistence."""
        data = asdict(self)
        # Convert dates back to isoformat strings for JSON/DB compatibility
        if self.filing_date:
            data["filing_date"] = self.filing_date.isoformat()
        if self.publication_date:
            data["publication_date"] = self.publication_date.isoformat()
        return data

    @classmethod
    def from_bigquery_row(cls, row: Dict[str, Any]) -> "Patent":
        """Create a Patent instance from a BigQuery result row.

        Expected keys (as emitted by the query builder):
        - publication_number (str)
        - title (str)
        - abstract (str)
        - filing_date (int YYYYMMDD)
        - publication_date (int YYYYMMDD)
        - country_code (str)
        - kind_code (str)
        - assignees (array<str>)
        - inventors (array<str>)
        - cpc_codes (array<str>)
        """
        return cls(
            publication_number=row.get("publication_number", "").strip(),
            title=(row.get("title") or "").strip(),
            abstract=(row.get("abstract") or "").strip(),
            filing_date=_parse_yyyymmdd(row.get("filing_date")),
            publication_date=_parse_yyyymmdd(row.get("publication_date")),
            assignees=[a for a in (row.get("assignees") or []) if a],
            inventors=[i for i in (row.get("inventors") or []) if i],
            cpc_codes=[c for c in (row.get("cpc_codes") or []) if c],
            country=row.get("country_code"),
            kind_code=row.get("kind_code"),
        )

    def is_valid_minimal(self) -> bool:
        """Validate minimal required fields for downstream processing."""
        if not self.publication_number:
            return False
        if not self.title or len(self.title) < 10:
            return False
        if not self.abstract or len(self.abstract) < 50:
            return False
        if not self.cpc_codes:
            return False
        return True


