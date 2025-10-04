"""
Unit tests for Agent P2 - Universal Relevance Filter.

Author: S.A.F.E. D.R.Y. A.R.C.H.I.T.E.C.T. System
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock

import pytest

from models import Patent, NewsArticle, RelevanceResult, normalize_category
from logic.relevance_heuristics import RelevanceHeuristics
from services.relevance_classifier import RelevanceClassifier
from agents.p2_relevance_filter import RelevanceFilterAgent


def load_labeled_fixtures() -> dict:
    """Load labeled test fixtures."""
    path = Path(__file__).parent / "fixtures" / "relevance" / "labeled_data.json"
    with open(path) as f:
        return json.load(f)


def create_patent_from_fixture(data: dict) -> Patent:
    """Create Patent object from fixture data."""
    return Patent(
        publication_number=data['publication_number'],
        title=data['title'],
        abstract=data['abstract'],
        filing_date=date.fromisoformat(data['filing_date']),
        publication_date=date.fromisoformat(data['publication_date']),
        assignees=data['assignees'],
        inventors=data['inventors'],
        cpc_codes=data['cpc_codes'],
        country=data['country'],
        kind_code=data['kind_code']
    )


def create_news_from_fixture(data: dict) -> NewsArticle:
    """Create NewsArticle object from fixture data."""
    return NewsArticle(
        source=data['source'],
        title=data['title'],
        link=data['link'],
        published_at=datetime.fromisoformat(data['published_at'].replace('Z', '+00:00')),
        summary=data['summary'],
        categories=data.get('categories', [])
    )


class TestRelevanceResult:
    """Test RelevanceResult model."""
    
    def test_result_serialization(self):
        """Test to_dict and from_dict."""
        result = RelevanceResult(
            item_id="test-123",
            source_type="patent",
            is_relevant=True,
            score=0.85,
            category="cloud",
            reasons=["Test reason"],
            model="gemini-2.5-flash",
            model_version="v1",
            timestamp=datetime.utcnow()
        )
        
        data = result.to_dict()
        assert 'timestamp' in data
        assert isinstance(data['timestamp'], str)
        
        restored = RelevanceResult.from_dict(data)
        assert restored.item_id == result.item_id
        assert restored.score == result.score
    
    def test_score_clamping(self):
        """Test score is clamped to [0, 1]."""
        result = RelevanceResult(
            item_id="test",
            source_type="news",
            is_relevant=True,
            score=1.5,  # Over 1.0
            category="malware",
            reasons=["test"],
            model="test",
            model_version="1.0",
            timestamp=datetime.utcnow()
        )
        assert result.score == 1.0
        
        result2 = RelevanceResult(
            item_id="test2",
            source_type="news",
            is_relevant=False,
            score=-0.5,  # Below 0.0
            category="unknown",
            reasons=["test"],
            model="test",
            model_version="1.0",
            timestamp=datetime.utcnow()
        )
        assert result2.score == 0.0
    
    def test_category_normalization(self):
        """Test category is normalized."""
        result = RelevanceResult(
            item_id="test",
            source_type="patent",
            is_relevant=True,
            score=0.8,
            category="  CLOUD  ",
            reasons=["test"],
            model="test",
            model_version="1.0",
            timestamp=datetime.utcnow()
        )
        assert result.category == "cloud"


class TestCategoryNormalization:
    """Test category normalization function."""
    
    def test_direct_match(self):
        """Test direct category matches."""
        assert normalize_category("cloud") == "cloud"
        assert normalize_category("malware") == "malware"
        assert normalize_category("identity") == "identity"
    
    def test_fuzzy_matching(self):
        """Test fuzzy category matching."""
        assert normalize_category("vuln") == "vulnerability"
        assert normalize_category("crypto") == "cryptography"
        assert normalize_category("iam") == "identity"
        assert normalize_category("threat") == "malware"
    
    def test_unknown_fallback(self):
        """Test unknown category fallback."""
        assert normalize_category("random_category") == "unknown"
        assert normalize_category("") == "unknown"


class TestRelevanceHeuristics:
    """Test heuristic-based classification."""
    
    def test_patent_with_security_cpc(self):
        """Test patent with security CPC codes."""
        fixtures = load_labeled_fixtures()
        patent_data = fixtures['patents'][0]  # Ransomware detection patent
        patent = create_patent_from_fixture(patent_data)
        
        heuristics = RelevanceHeuristics(min_score=0.5)
        result = heuristics.classify_patent(patent)
        
        assert result.is_relevant is True
        assert result.score >= 0.5
        assert result.model == "heuristic-v1"
        assert len(result.reasons) > 0
    
    def test_patent_without_security_cpc(self):
        """Test non-security patent."""
        fixtures = load_labeled_fixtures()
        patent_data = fixtures['patents'][2]  # E-commerce patent
        patent = create_patent_from_fixture(patent_data)
        
        heuristics = RelevanceHeuristics(min_score=0.5)
        result = heuristics.classify_patent(patent)
        
        assert result.is_relevant is False or result.score < 0.5
    
    def test_news_with_security_keywords(self):
        """Test news with strong security signals."""
        fixtures = load_labeled_fixtures()
        news_data = fixtures['news'][1]  # Zero-day CVE article
        article = create_news_from_fixture(news_data)
        
        heuristics = RelevanceHeuristics(min_score=0.5)
        result = heuristics.classify_news(article)
        
        assert result.is_relevant is True
        assert result.score >= 0.5
        assert len(result.reasons) > 0
    
    def test_news_without_security_keywords(self):
        """Test non-security news."""
        fixtures = load_labeled_fixtures()
        news_data = fixtures['news'][2]  # Food delivery M&A
        article = create_news_from_fixture(news_data)
        
        heuristics = RelevanceHeuristics(min_score=0.5)
        result = heuristics.classify_news(article)
        
        assert result.is_relevant is False or result.score < 0.5


class TestRelevanceClassifier:
    """Test RelevanceClassifier service."""
    
    @patch('clients.gemini_client.GeminiClient.generate_content')
    def test_llm_classification_success(self, mock_generate):
        """Test successful LLM classification."""
        # Mock LLM response
        mock_generate.return_value = json.dumps({
            "is_relevant": True,
            "score": 0.9,
            "category": "malware",
            "reasons": ["Ransomware detection", "ML-based threat analysis"],
            "model": "gemini-2.5-flash",
            "model_version": "v1"
        })
        
        fixtures = load_labeled_fixtures()
        patent_data = fixtures['patents'][0]
        patent = create_patent_from_fixture(patent_data)
        
        classifier = RelevanceClassifier(enable_cache=False)
        result = classifier.classify(patent, use_llm=True)
        
        assert result.is_relevant is True
        assert result.score == 0.9
        assert result.category == "malware"
        assert result.model == "gemini-2.5-flash"
    
    @patch('clients.gemini_client.GeminiClient.generate_content')
    def test_llm_failure_fallback_to_heuristic(self, mock_generate):
        """Test fallback to heuristics when LLM fails."""
        # Mock LLM failure
        mock_generate.side_effect = Exception("API timeout")
        
        fixtures = load_labeled_fixtures()
        patent_data = fixtures['patents'][0]
        patent = create_patent_from_fixture(patent_data)
        
        classifier = RelevanceClassifier(enable_cache=False, enable_fallback=True)
        result = classifier.classify(patent, use_llm=True)
        
        # Should fallback to heuristics
        assert result.model == "heuristic-v1"
        assert isinstance(result.score, float)
    
    def test_cache_functionality(self):
        """Test result caching."""
        fixtures = load_labeled_fixtures()
        patent_data = fixtures['patents'][0]
        patent = create_patent_from_fixture(patent_data)
        
        classifier = RelevanceClassifier(enable_cache=True)
        
        # First call (heuristic, no LLM)
        result1 = classifier.classify(patent, use_llm=False)
        cache_size_1 = classifier.get_cache_size()
        
        # Second call (should hit cache)
        result2 = classifier.classify(patent, use_llm=False)
        cache_size_2 = classifier.get_cache_size()
        
        assert result1.hash == result2.hash
        assert cache_size_1 == cache_size_2  # No new cache entry


class TestRelevanceFilterAgent:
    """Test Agent P2 end-to-end."""
    
    def test_filter_items_heuristic_only(self):
        """Test filtering with heuristics only (no LLM)."""
        fixtures = load_labeled_fixtures()
        
        # Mix of relevant and not relevant items
        items = [
            create_patent_from_fixture(fixtures['patents'][0]),  # Relevant
            create_patent_from_fixture(fixtures['patents'][2]),  # Not relevant
            create_news_from_fixture(fixtures['news'][1]),       # Relevant
            create_news_from_fixture(fixtures['news'][2]),       # Not relevant
        ]
        
        agent = RelevanceFilterAgent(min_score=0.5, max_workers=1)
        results, stats = agent.filter_items(items, use_llm=False)
        
        assert len(results) == 4
        assert stats['total_items'] == 4
        assert stats['heuristic_fallback'] == 4
        assert stats['llm_used'] == 0
        
        relevant = agent.get_relevant_items(results)
        assert len(relevant) >= 1  # At least some should be relevant
    
    @patch('clients.gemini_client.GeminiClient.generate_content')
    def test_filter_items_with_llm(self, mock_generate):
        """Test filtering with LLM."""
        # Mock LLM to return relevant for security items
        def mock_llm_response(prompt, **kwargs):
            if "ransomware" in prompt.lower() or "zero-day" in prompt.lower():
                return json.dumps({
                    "is_relevant": True,
                    "score": 0.9,
                    "category": "malware",
                    "reasons": ["Security technology"],
                    "model": "gemini-2.5-flash",
                    "model_version": "v1"
                })
            else:
                return json.dumps({
                    "is_relevant": False,
                    "score": 0.1,
                    "category": "unknown",
                    "reasons": ["No security relevance"],
                    "model": "gemini-2.5-flash",
                    "model_version": "v1"
                })
        
        mock_generate.side_effect = mock_llm_response
        
        fixtures = load_labeled_fixtures()
        items = [
            create_patent_from_fixture(fixtures['patents'][0]),  # Ransomware - relevant
            create_patent_from_fixture(fixtures['patents'][2]),  # E-commerce - not relevant
        ]
        
        agent = RelevanceFilterAgent(min_score=0.6, max_workers=1)
        results, stats = agent.filter_items(items, use_llm=True)
        
        assert len(results) == 2
        assert stats['llm_used'] == 2
        
        relevant = agent.get_relevant_items(results)
        assert len(relevant) >= 1


class TestPrecisionOnLabeledData:
    """Test precision on labeled dataset (≥70% requirement)."""
    
    def test_heuristic_precision(self):
        """Test heuristic classifier precision on labeled data."""
        fixtures = load_labeled_fixtures()
        
        # Load all labeled items
        patents = [create_patent_from_fixture(p) for p in fixtures['patents']]
        news = [create_news_from_fixture(n) for n in fixtures['news']]
        all_items = patents + news
        
        # Get ground truth labels
        ground_truth = (
            [p['label'] == 'relevant' for p in fixtures['patents']] +
            [n['label'] == 'relevant' for n in fixtures['news']]
        )
        
        # Classify with heuristics
        agent = RelevanceFilterAgent(min_score=0.5, max_workers=1)
        results, stats = agent.filter_items(all_items, use_llm=False)
        
        # Calculate precision: TP / (TP + FP)
        predictions = [r.is_relevant and r.score >= 0.5 for r in results]
        
        true_positives = sum(1 for pred, truth in zip(predictions, ground_truth) if pred and truth)
        false_positives = sum(1 for pred, truth in zip(predictions, ground_truth) if pred and not truth)
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        
        print(f"\nHeuristic Precision: {precision:.2%}")
        print(f"True Positives: {true_positives}")
        print(f"False Positives: {false_positives}")
        print(f"Total Predictions: {sum(predictions)}")
        
        # Assert ≥70% precision (success criterion)
        assert precision >= 0.70, f"Precision {precision:.2%} is below 70% threshold"

