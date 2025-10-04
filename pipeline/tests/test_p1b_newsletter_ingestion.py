"""
Unit tests for Agent P1b - Newsletter Ingestion.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime

import pytest

from models.news_article import NewsArticle
from parsers.feed_parser import FeedParser
from logic.funding_detector import FundingDetector
from agents.p1b_newsletter_ingestion import NewsletterIngestionAgent


def load_fixture_xml() -> str:
    """Load sample RSS XML fixture."""
    path = Path(__file__).parent / "fixtures" / "rss" / "sample_feed.xml"
    with open(path) as f:
        return f.read()


class TestNewsArticleModel:
    """Test NewsArticle data model."""
    
    def test_article_id_generation(self):
        """Test stable ID generation."""
        article1 = NewsArticle(
            source="TestSource",
            title="Test Article",
            link="https://example.com/article1",
            published_at=datetime.utcnow()
        )
        article2 = NewsArticle(
            source="TestSource",
            title="Test Article",
            link="https://example.com/article1",
            published_at=datetime.utcnow()
        )
        # Same source+link should have same ID
        assert article1.id == article2.id
    
    def test_to_dict_serialization(self):
        """Test dictionary serialization."""
        article = NewsArticle(
            source="TestSource",
            title="Test",
            link="https://example.com",
            published_at=datetime.utcnow()
        )
        data = article.to_dict()
        assert 'id' in data
        assert 'published_at' in data
        assert isinstance(data['published_at'], str)  # ISO format


class TestFundingDetector:
    """Test funding announcement detection."""
    
    def test_positive_funding_announcement(self):
        """Test detection of funding announcements."""
        detector = FundingDetector(min_signals=2)
        
        # Clear funding announcement
        text = "Wiz announced today it raised $100 million in Series B funding led by Insight Partners."
        is_funding, reason = detector.detect(text)
        assert is_funding is True
        assert "action" in reason
        assert "money" in reason
        
    def test_negative_non_funding(self):
        """Test non-funding articles are not flagged."""
        detector = FundingDetector(min_signals=2)
        
        # Security advisory (no funding)
        text = "A critical vulnerability was discovered in Apache Log4j affecting versions 2.0 through 2.14."
        is_funding, reason = detector.detect(text)
        assert is_funding is False
    
    def test_partial_signals_below_threshold(self):
        """Test that single signal is insufficient."""
        detector = FundingDetector(min_signals=2)
        
        # Only mentions money, no action/stage/investor (just one signal)
        text = "The cybersecurity market is worth $100 million globally."
        is_funding, reason = detector.detect(text)
        assert is_funding is False


class TestFeedParser:
    """Test RSS feed parsing."""
    
    @patch('feedparser.parse')
    def test_parse_feed_with_date_filter(self, mock_parse):
        """Test feed parsing with date filtering."""
        # Mock feedparser response
        mock_parse.return_value = {
            'entries': [
                {
                    'title': 'Recent Article',
                    'link': 'https://example.com/recent',
                    'published_parsed': datetime.utcnow().timetuple(),
                    'summary': 'Recent article summary'
                }
            ]
        }
        
        parser = FeedParser(lookback_days=7)
        articles = parser.parse_feed(mock_parse.return_value, "TestSource")
        
        assert len(articles) > 0
        assert articles[0].source == "TestSource"


class TestNewsletterIngestionAgent:
    """Test Agent P1b end-to-end."""
    
    @patch('clients.rss_client.RSSClient.fetch_feed')
    def test_fetch_articles_success(self, mock_fetch):
        """Test successful article fetching."""
        # Mock RSS response
        mock_fetch.return_value = {
            'entries': [
                {
                    'title': 'Startup raises $50M Series A led by Accel',
                    'link': f'https://example.com/article{i}',
                    'published_parsed': datetime.utcnow().timetuple(),
                    'summary': 'Startup announced $50M Series A funding led by Accel Partners.'
                }
                for i in range(30)  # Generate 30 articles per feed
            ]
        }
        
        agent = NewsletterIngestionAgent(
            lookback_days=7,
            fetch_content=False,  # Disable content fetching for speed
            min_articles=50
        )
        
        articles = agent.fetch_articles()
        
        assert len(articles) >= 50
        assert all(isinstance(a, NewsArticle) for a in articles)
        
        stats = agent.get_statistics()
        assert stats['feeds_processed'] > 0
        assert stats['funding_flagged'] > 0  # Some should be detected
    
    @patch('clients.rss_client.RSSClient.fetch_feed')
    def test_handles_feed_failures_gracefully(self, mock_fetch):
        """Test agent continues when some feeds fail."""
        # First call fails, second succeeds
        mock_fetch.side_effect = [
            Exception("Network error"),
            {
                'entries': [
                    {
                        'title': f'Article {i}',
                        'link': f'https://example.com/article{i}',
                        'published_parsed': datetime.utcnow().timetuple(),
                        'summary': 'Test summary'
                    }
                    for i in range(40)
                ]
            }
        ] * 2  # Repeat for multiple feeds
        
        agent = NewsletterIngestionAgent(
            lookback_days=7,
            fetch_content=False,
            min_articles=50
        )
        
        articles = agent.fetch_articles()
        
        # Should have articles despite some failures
        assert len(articles) > 0
        stats = agent.get_statistics()
        assert stats['feeds_failed'] > 0

