"""
Entities and Entity Aliases Repository
Maps ResolvedEntity and AliasLink domain models to database schema
"""
import logging
from typing import List, Dict, Any

from models.entities import ResolvedEntity, AliasLink
from clients.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class EntitiesRepository:
    """Repository for entities and entity_aliases tables"""
    
    ENTITIES_TABLE = 'entities'
    ALIASES_TABLE = 'entity_aliases'
    
    def __init__(self):
        self.client = get_supabase_client()
    
    @staticmethod
    def _entity_to_db_dict(entity: ResolvedEntity) -> Dict[str, Any]:
        """
        Convert ResolvedEntity model to database dict
        
        Args:
            entity: ResolvedEntity domain model
        
        Returns:
            Dict matching entities table schema
        """
        return {
            'entity_id': entity.entity_id,
            'canonical_name': entity.canonical_name,
            'sources': entity.sources or [],
            'confidence': entity.confidence,
        }
    
    @staticmethod
    def _alias_to_db_dict(alias: AliasLink) -> Dict[str, Any]:
        """
        Convert AliasLink model to database dict
        
        Args:
            alias: AliasLink domain model
        
        Returns:
            Dict matching entity_aliases table schema
        """
        return {
            'raw_name': alias.raw_name,
            'entity_id': alias.entity_id,
            'score': alias.score,
            'rules_applied': alias.rules_applied or [],
        }
    
    def upsert_entities(self, entities: List[ResolvedEntity]) -> Dict[str, Any]:
        """
        Upsert entities in batches
        
        Args:
            entities: List of ResolvedEntity models
        
        Returns:
            Dict with 'count' (rows written) and 'success' (bool)
        """
        if not entities:
            logger.warning("upsert_entities called with empty list")
            return {'count': 0, 'success': True}
        
        logger.info(f"Upserting {len(entities)} entities")
        
        try:
            # Convert to DB format
            rows = [self._entity_to_db_dict(e) for e in entities]
            
            # Batch upsert
            result = self.client.upsert_batch(
                table=self.ENTITIES_TABLE,
                rows=rows,
                on_conflict='entity_id',
                returning='minimal'
            )
            
            count = result.get('count', 0)
            logger.info(f"Successfully upserted {count} entities")
            
            return {
                'count': count,
                'success': True,
                'table': self.ENTITIES_TABLE
            }
        
        except Exception as e:
            logger.error(f"Failed to upsert entities: {e}", exc_info=True)
            return {
                'count': 0,
                'success': False,
                'error': str(e),
                'table': self.ENTITIES_TABLE
            }
    
    def upsert_aliases(self, aliases: List[AliasLink]) -> Dict[str, Any]:
        """
        Upsert entity aliases in batches
        
        Args:
            aliases: List of AliasLink models
        
        Returns:
            Dict with 'count' (rows written) and 'success' (bool)
        """
        if not aliases:
            logger.warning("upsert_aliases called with empty list")
            return {'count': 0, 'success': True}
        
        logger.info(f"Upserting {len(aliases)} entity aliases")
        
        try:
            # Convert to DB format
            rows = [self._alias_to_db_dict(a) for a in aliases]
            
            # Batch upsert
            result = self.client.upsert_batch(
                table=self.ALIASES_TABLE,
                rows=rows,
                on_conflict='raw_name',
                returning='minimal'
            )
            
            count = result.get('count', 0)
            logger.info(f"Successfully upserted {count} entity aliases")
            
            return {
                'count': count,
                'success': True,
                'table': self.ALIASES_TABLE
            }
        
        except Exception as e:
            logger.error(f"Failed to upsert entity aliases: {e}", exc_info=True)
            return {
                'count': 0,
                'success': False,
                'error': str(e),
                'table': self.ALIASES_TABLE
            }
    
    def get_entity_by_id(self, entity_id: str) -> Dict[str, Any]:
        """
        Get entity by ID
        
        Args:
            entity_id: Entity ID
        
        Returns:
            Entity dict or empty dict if not found
        """
        results = self.client.select(
            table=self.ENTITIES_TABLE,
            filters={'entity_id': entity_id},
            limit=1
        )
        return results[0] if results else {}
    
    def get_aliases_by_entity(self, entity_id: str) -> List[Dict[str, Any]]:
        """
        Get all aliases for an entity
        
        Args:
            entity_id: Entity ID
        
        Returns:
            List of alias dicts
        """
        return self.client.select(
            table=self.ALIASES_TABLE,
            filters={'entity_id': entity_id}
        )

