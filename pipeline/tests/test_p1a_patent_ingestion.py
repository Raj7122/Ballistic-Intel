from __future__ import annotations

import json
from pathlib import Path
from typing import List
from unittest.mock import Mock

import pytest

from agents.p1a_patent_ingestion import PatentIngestionAgent, PatentIngestionError
from models.patent import Patent
from agents.query_builder import PatentQueryBuilder


def load_fixture_rows() -> List[dict]:
    path = Path(__file__).parent / "fixtures" / "patents.json"
    with open(path) as f:
        return json.load(f)


class TestPatentModel:
    def test_patent_from_bigquery_row_and_validation(self):
        row = load_fixture_rows()[0]
        patent = Patent.from_bigquery_row(row)
        assert patent.publication_number.startswith("US-")
        assert patent.is_valid_minimal() is True
        d = patent.to_dict()
        assert isinstance(d["filing_date"], str)


class TestQueryBuilder:
    def test_date_range_format(self):
        qb = PatentQueryBuilder(lookback_days=7)
        start, end = qb.get_date_range()
        assert len(start) == 8 and len(end) == 8

    def test_build_patent_query_contains_filters(self):
        qb = PatentQueryBuilder(lookback_days=7)
        start, end = qb.get_date_range()
        sql = qb.build_patent_query(start, end)
        assert "patents-public-data.patents.publications" in sql
        assert "H04L%" in sql and "G06F21%" in sql


class TestPatentIngestionAgent:
    @pytest.fixture
    def mock_bq_client(self):
        client = Mock()
        client.bytes_processed = 123456
        client.execute_query.return_value = load_fixture_rows() * 30  # >= 60 items
        return client

    def test_fetch_patents_success(self, mock_bq_client):
        agent = PatentIngestionAgent(mock_bq_client, lookback_days=7, min_patents=50)
        patents = agent.fetch_patents()
        assert len(patents) >= 50
        assert all(isinstance(p, Patent) for p in patents)
        stats = agent.get_statistics()
        assert stats["patents_fetched"] >= 50
        assert stats["bytes_processed"] == 123456

    def test_fallback_when_insufficient(self, mock_bq_client):
        # First call returns few rows, second returns many
        few = load_fixture_rows()[:1]
        many = load_fixture_rows() * 30
        mock_bq_client.execute_query.side_effect = [few, many]
        agent = PatentIngestionAgent(mock_bq_client, min_patents=50)
        patents = agent.fetch_patents()
        assert len(patents) >= 50
        assert mock_bq_client.execute_query.call_count == 2

    def test_raises_on_total_failure(self, mock_bq_client):
        mock_bq_client.execute_query.return_value = []
        agent = PatentIngestionAgent(mock_bq_client, min_patents=50)
        with pytest.raises(PatentIngestionError):
            agent.fetch_patents()


