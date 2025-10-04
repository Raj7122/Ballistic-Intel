"""
Storage Writer Service
High-level interface for persisting all agent outputs
"""
import logging
from typing import List, Dict, Any, Union

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

logger = logging.getLogger(__name__)


class StorageWriter:
    """Orchestrates persistence of all agent outputs"""
    
    def __init__(self):
        self.patents_repo = PatentsRepository()
        self.news_repo = NewsRepository()
        self.relevance_repo = RelevanceRepository()
        self.extraction_repo = ExtractionRepository()
        self.entities_repo = EntitiesRepository()
    
    def persist_patents(self, patents: List[Patent]) -> Dict[str, Any]:
        """
        Persist patents from Agent P1a
        
        Args:
            patents: List of Patent models
        
        Returns:
            Result dict with count and success status
        """
        logger.info(f"[StorageWriter] Persisting {len(patents)} patents")
        result = self.patents_repo.upsert_patents(patents)
        
        if result['success']:
            logger.info(f"[StorageWriter] ✓ Patents persisted: {result['count']}")
        else:
            logger.error(f"[StorageWriter] ✗ Failed to persist patents: {result.get('error')}")
        
        return result
    
    def persist_news(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Persist news articles from Agent P1b
        
        Args:
            articles: List of NewsArticle models
        
        Returns:
            Result dict with count and success status
        """
        logger.info(f"[StorageWriter] Persisting {len(articles)} news articles")
        result = self.news_repo.upsert_news(articles)
        
        if result['success']:
            logger.info(f"[StorageWriter] ✓ News articles persisted: {result['count']}")
        else:
            logger.error(f"[StorageWriter] ✗ Failed to persist news articles: {result.get('error')}")
        
        return result
    
    def persist_relevance(self, results: List[RelevanceResult]) -> Dict[str, Any]:
        """
        Persist relevance results from Agent P2
        
        Args:
            results: List of RelevanceResult models
        
        Returns:
            Result dict with count and success status
        """
        logger.info(f"[StorageWriter] Persisting {len(results)} relevance results")
        result = self.relevance_repo.upsert_relevance(results)
        
        if result['success']:
            logger.info(f"[StorageWriter] ✓ Relevance results persisted: {result['count']}")
        else:
            logger.error(f"[StorageWriter] ✗ Failed to persist relevance results: {result.get('error')}")
        
        return result
    
    def persist_extractions(self, results: List[ExtractionResult]) -> Dict[str, Any]:
        """
        Persist extraction results from Agent P3
        
        Args:
            results: List of ExtractionResult models
        
        Returns:
            Result dict with count and success status
        """
        logger.info(f"[StorageWriter] Persisting {len(results)} extraction results")
        result = self.extraction_repo.upsert_extractions(results)
        
        if result['success']:
            logger.info(f"[StorageWriter] ✓ Extraction results persisted: {result['count']}")
        else:
            logger.error(f"[StorageWriter] ✗ Failed to persist extraction results: {result.get('error')}")
        
        return result
    
    def persist_entities(
        self, 
        entities: List[ResolvedEntity],
        aliases: List[AliasLink]
    ) -> Dict[str, Any]:
        """
        Persist entities and aliases from Agent P4
        
        Args:
            entities: List of ResolvedEntity models
            aliases: List of AliasLink models
        
        Returns:
            Combined result dict
        """
        logger.info(f"[StorageWriter] Persisting {len(entities)} entities and {len(aliases)} aliases")
        
        # Persist entities first
        entities_result = self.entities_repo.upsert_entities(entities)
        
        # Then persist aliases (they reference entities via FK)
        aliases_result = self.entities_repo.upsert_aliases(aliases)
        
        combined_success = entities_result['success'] and aliases_result['success']
        
        if combined_success:
            logger.info(
                f"[StorageWriter] ✓ Entities persisted: {entities_result['count']} entities, "
                f"{aliases_result['count']} aliases"
            )
        else:
            logger.error(
                f"[StorageWriter] ✗ Failed to persist entities/aliases: "
                f"entities={entities_result.get('error')}, aliases={aliases_result.get('error')}"
            )
        
        return {
            'entities': entities_result,
            'aliases': aliases_result,
            'success': combined_success,
            'total_count': entities_result['count'] + aliases_result['count']
        }
    
    def persist_all(
        self,
        patents: List[Patent] = None,
        news: List[NewsArticle] = None,
        relevance: List[RelevanceResult] = None,
        extractions: List[ExtractionResult] = None,
        entities: List[ResolvedEntity] = None,
        aliases: List[AliasLink] = None
    ) -> Dict[str, Any]:
        """
        Persist all agent outputs in a single call
        
        Args:
            patents: Optional list of patents
            news: Optional list of news articles
            relevance: Optional list of relevance results
            extractions: Optional list of extraction results
            entities: Optional list of entities
            aliases: Optional list of aliases
        
        Returns:
            Combined result dict with all statuses
        """
        results = {}
        
        if patents:
            results['patents'] = self.persist_patents(patents)
        
        if news:
            results['news'] = self.persist_news(news)
        
        if relevance:
            results['relevance'] = self.persist_relevance(relevance)
        
        if extractions:
            results['extractions'] = self.persist_extractions(extractions)
        
        if entities or aliases:
            results['entities'] = self.persist_entities(
                entities or [],
                aliases or []
            )
        
        overall_success = all(
            r.get('success', False) for r in results.values()
        )
        
        total_count = sum(
            r.get('count', r.get('total_count', 0)) for r in results.values()
        )
        
        logger.info(
            f"[StorageWriter] Batch persist complete: "
            f"{total_count} total rows, success={overall_success}"
        )
        
        return {
            'results': results,
            'success': overall_success,
            'total_count': total_count
        }


# Singleton instance
_writer_instance: Union[StorageWriter, None] = None


def get_storage_writer() -> StorageWriter:
    """Get or create the singleton StorageWriter"""
    global _writer_instance
    if _writer_instance is None:
        _writer_instance = StorageWriter()
    return _writer_instance

