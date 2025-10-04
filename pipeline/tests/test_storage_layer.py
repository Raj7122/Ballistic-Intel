"""
Unit Tests for Storage Layer (Repositories)
Tests upsert mapping logic with mocked Supabase client
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import date, datetime, UTC

from models.patent import Patent
from models.news_article import NewsArticle
from models.relevance import RelevanceResult
from models.extraction import ExtractionResult
from models.entities import ResolvedEntity, AliasLink

from repos.patents_repo import PatentsRepository
from repos.news_repo import NewsRepository
from repos.relevance_repo import RelevanceRepository
from repos.extraction_repo import ExtractionRepository
from repos.entities_repo import EntitiesRepository
from services.storage_writer import StorageWriter


class TestPatentsRepository:
    """Test PatentsRepository mapping and upsert"""
    
    def test_to_db_dict(self):
        """Test Patent model to DB dict conversion"""
        patent = Patent(
            publication_number='US-2024-123456-A1',
            title='Test Patent',
            abstract='Test abstract',
            filing_date=date(2024, 1, 1),
            publication_date=date(2024, 6, 1),
            assignees=['Test Corp'],
            inventors=['John Doe'],
            cpc_codes=['H04L9/00'],
            country='US',
            kind_code='A1'
        )
        
        db_dict = PatentsRepository._to_db_dict(patent)
        
        assert db_dict['publication_number'] == 'US-2024-123456-A1'
        assert db_dict['title'] == 'Test Patent'
        assert db_dict['filing_date'] == '2024-01-01'
        assert db_dict['publication_date'] == '2024-06-01'
        assert db_dict['assignees'] == ['Test Corp']
        assert db_dict['cpc_codes'] == ['H04L9/00']
    
    @patch('repos.patents_repo.get_supabase_client')
    def test_upsert_patents_success(self, mock_get_client):
        """Test successful patents upsert"""
        # Mock client
        mock_client = Mock()
        mock_client.upsert_batch.return_value = {'count': 2, 'data': []}
        mock_get_client.return_value = mock_client
        
        # Test data
        patents = [
            Patent(
                publication_number='US-2024-123456-A1',
                title='Patent 1',
                abstract='Abstract 1',
                filing_date=date(2024, 1, 1),
                publication_date=date(2024, 6, 1),
                assignees=['Corp A'],
                inventors=['Alice'],
                cpc_codes=['H04L9/00'],
                country='US',
                kind_code='A1'
            ),
            Patent(
                publication_number='US-2024-123457-A1',
                title='Patent 2',
                abstract='Abstract 2',
                filing_date=date(2024, 2, 1),
                publication_date=date(2024, 7, 1),
                assignees=['Corp B'],
                inventors=['Bob'],
                cpc_codes=['G06F21/00'],
                country='US',
                kind_code='A1'
            )
        ]
        
        repo = PatentsRepository()
        result = repo.upsert_patents(patents)
        
        assert result['success'] is True
        assert result['count'] == 2
        assert result['table'] == 'patents'
        
        # Verify client called with correct args
        mock_client.upsert_batch.assert_called_once()
        call_args = mock_client.upsert_batch.call_args
        assert call_args.kwargs['table'] == 'patents'
        assert call_args.kwargs['on_conflict'] == 'publication_number'
        assert len(call_args.kwargs['rows']) == 2


class TestNewsRepository:
    """Test NewsRepository mapping and upsert"""
    
    def test_to_db_dict(self):
        """Test NewsArticle model to DB dict conversion"""
        article = NewsArticle(
            source='TechCrunch',
            title='Test Article',
            link='https://example.com/article',
            published_at=datetime(2024, 1, 15, 12, 0, 0),
            summary='Test summary',
            categories=['funding', 'startup'],
            content_text='Full article text'
        )
        
        db_dict = NewsRepository._to_db_dict(article)
        
        assert db_dict['id'] == article.id  # ID is generated
        assert db_dict['source'] == 'TechCrunch'
        assert db_dict['link'] == 'https://example.com/article'
        assert '2024-01-15' in db_dict['published_at']
        assert db_dict['categories'] == ['funding', 'startup']
    
    @patch('repos.news_repo.get_supabase_client')
    def test_upsert_news_success(self, mock_get_client):
        """Test successful news articles upsert"""
        mock_client = Mock()
        mock_client.upsert_batch.return_value = {'count': 1, 'data': []}
        mock_get_client.return_value = mock_client
        
        articles = [
            NewsArticle(
                source='VentureBeat',
                title='Startup Raises $10M',
                link='https://example.com/startup-funding',
                published_at=datetime(2024, 3, 1, 10, 0, 0),
                summary='Startup secures funding',
                categories=['funding'],
                content_text='Full text'
            )
        ]
        
        repo = NewsRepository()
        result = repo.upsert_news(articles)
        
        assert result['success'] is True
        assert result['count'] == 1
        
        call_args = mock_client.upsert_batch.call_args
        assert call_args.kwargs['on_conflict'] == 'link'


class TestRelevanceRepository:
    """Test RelevanceRepository mapping and upsert"""
    
    def test_to_db_dict(self):
        """Test RelevanceResult model to DB dict conversion"""
        result = RelevanceResult(
            item_id='US-2024-123456-A1',
            source_type='patent',
            is_relevant=True,
            score=0.95,
            category='cybersecurity',
            reasons=['Strong CPC match', 'Keyword match'],
            model='gemini-2.5-flash',
            model_version='1.0',
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        db_dict = RelevanceRepository._to_db_dict(result)
        
        assert db_dict['item_id'] == 'US-2024-123456-A1'
        assert db_dict['source_type'] == 'patent'
        assert db_dict['is_relevant'] is True
        assert db_dict['score'] == 0.95
        assert db_dict['category'] == 'cybersecurity'
        assert len(db_dict['reasons']) == 2
    
    @patch('repos.relevance_repo.get_supabase_client')
    def test_upsert_relevance_success(self, mock_get_client):
        """Test successful relevance results upsert"""
        mock_client = Mock()
        mock_client.upsert_batch.return_value = {'count': 1, 'data': []}
        mock_get_client.return_value = mock_client
        
        results = [
            RelevanceResult(
                item_id='US-2024-123456-A1',
                source_type='patent',
                is_relevant=True,
                score=0.92,
                category='cybersecurity',
                reasons=['CPC match'],
                model='gemini-2.5-flash',
                model_version='1.0',
                timestamp=datetime.now(UTC)
            )
        ]
        
        repo = RelevanceRepository()
        result = repo.upsert_relevance(results)
        
        assert result['success'] is True
        assert result['count'] == 1
        
        call_args = mock_client.upsert_batch.call_args
        assert 'item_id' in call_args.kwargs['on_conflict']


class TestExtractionRepository:
    """Test ExtractionRepository mapping and upsert"""
    
    def test_to_db_dict(self):
        """Test ExtractionResult model to DB dict conversion"""
        result = ExtractionResult(
            item_id='US-2024-123456-A1',
            source_type='patent',
            company_names=['Acme Corp', 'Beta Inc'],
            sector='identity',  # Valid category from VALID_CATEGORIES
            novelty_score=0.85,
            tech_keywords=['authentication', 'biometric', 'encryption'],
            rationale=['Biometric auth system', 'Novel algorithm'],
            model='gemini-2.5-flash',
            model_version='1.0',
            timestamp=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        db_dict = ExtractionRepository._to_db_dict(result)
        
        assert db_dict['item_id'] == 'US-2024-123456-A1'
        assert len(db_dict['company_names']) == 2
        assert db_dict['sector'] == 'identity'  # Normalized category
        assert db_dict['novelty_score'] == 0.85
        assert len(db_dict['tech_keywords']) == 3
    
    @patch('repos.extraction_repo.get_supabase_client')
    def test_upsert_extractions_success(self, mock_get_client):
        """Test successful extraction results upsert"""
        mock_client = Mock()
        mock_client.upsert_batch.return_value = {'count': 1, 'data': []}
        mock_get_client.return_value = mock_client
        
        results = [
            ExtractionResult(
                item_id='xyz789',
                source_type='news',
                company_names=['Startup X'],
                sector='Cloud Security',
                novelty_score=0.75,
                tech_keywords=['cloud', 'zero-trust'],
                rationale=['Funding announcement'],
                model='gemini-2.5-flash',
                model_version='1.0',
                timestamp=datetime.now(UTC)
            )
        ]
        
        repo = ExtractionRepository()
        result = repo.upsert_extractions(results)
        
        assert result['success'] is True
        assert result['count'] == 1


class TestEntitiesRepository:
    """Test EntitiesRepository mapping and upsert"""
    
    def test_entity_to_db_dict(self):
        """Test ResolvedEntity model to DB dict conversion"""
        entity = ResolvedEntity(
            entity_id='ent_abc123',
            canonical_name='Acme Corporation',
            aliases=['ACME Corp', 'Acme Inc'],
            sources=['patent', 'news'],
            confidence=0.95,
            created_at=datetime(2024, 1, 1, 12, 0, 0)
        )
        
        db_dict = EntitiesRepository._entity_to_db_dict(entity)
        
        assert db_dict['entity_id'] == 'ent_abc123'
        assert db_dict['canonical_name'] == 'Acme Corporation'
        assert db_dict['sources'] == ['patent', 'news']
        assert db_dict['confidence'] == 0.95
    
    def test_alias_to_db_dict(self):
        """Test AliasLink model to DB dict conversion"""
        alias = AliasLink(
            raw_name='ACME Corp.',
            canonical_name='Acme Corporation',
            entity_id='ent_abc123',
            score=0.92,
            rules_applied=['normalize', 'remove_suffix']
        )
        
        db_dict = EntitiesRepository._alias_to_db_dict(alias)
        
        assert db_dict['raw_name'] == 'ACME Corp.'
        assert db_dict['entity_id'] == 'ent_abc123'
        assert db_dict['score'] == 0.92
        assert len(db_dict['rules_applied']) == 2
    
    @patch('repos.entities_repo.get_supabase_client')
    def test_upsert_entities_and_aliases(self, mock_get_client):
        """Test successful entities and aliases upsert"""
        mock_client = Mock()
        mock_client.upsert_batch.return_value = {'count': 1, 'data': []}
        mock_get_client.return_value = mock_client
        
        entities = [
            ResolvedEntity(
                entity_id='ent_001',
                canonical_name='Beta Systems',
                aliases=['Beta Systems Inc', 'Beta'],
                sources=['patent'],
                confidence=0.88,
                created_at=datetime(2024, 1, 1, 12, 0, 0)
            )
        ]
        
        aliases = [
            AliasLink(
                raw_name='Beta Systems Inc',
                canonical_name='Beta Systems',
                entity_id='ent_001',
                score=0.90,
                rules_applied=['remove_suffix']
            )
        ]
        
        repo = EntitiesRepository()
        
        entities_result = repo.upsert_entities(entities)
        assert entities_result['success'] is True
        
        aliases_result = repo.upsert_aliases(aliases)
        assert aliases_result['success'] is True


class TestStorageWriter:
    """Test StorageWriter orchestration"""
    
    @patch('services.storage_writer.PatentsRepository')
    @patch('services.storage_writer.NewsRepository')
    @patch('services.storage_writer.RelevanceRepository')
    @patch('services.storage_writer.ExtractionRepository')
    @patch('services.storage_writer.EntitiesRepository')
    def test_persist_all(
        self,
        mock_entities_repo,
        mock_extraction_repo,
        mock_relevance_repo,
        mock_news_repo,
        mock_patents_repo
    ):
        """Test persist_all orchestration"""
        # Mock all repos
        mock_patents_repo.return_value.upsert_patents.return_value = {
            'count': 5, 'success': True
        }
        mock_news_repo.return_value.upsert_news.return_value = {
            'count': 3, 'success': True
        }
        mock_relevance_repo.return_value.upsert_relevance.return_value = {
            'count': 8, 'success': True
        }
        mock_extraction_repo.return_value.upsert_extractions.return_value = {
            'count': 8, 'success': True
        }
        mock_entities_repo.return_value.upsert_entities.return_value = {
            'count': 4, 'success': True
        }
        mock_entities_repo.return_value.upsert_aliases.return_value = {
            'count': 10, 'success': True
        }
        
        writer = StorageWriter()
        
        # Test with minimal data
        patents = [Patent(
            publication_number='US-2024-999999-A1',
            title='Test',
            abstract='Test',
            filing_date=date(2024, 1, 1),
            publication_date=date(2024, 6, 1),
            assignees=[],
            inventors=[],
            cpc_codes=[],
            country='US',
            kind_code='A1'
        )]
        
        result = writer.persist_all(patents=patents)
        
        assert result['success'] is True
        assert 'results' in result
        assert 'patents' in result['results']
        assert result['results']['patents']['count'] == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

