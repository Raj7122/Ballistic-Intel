from .patent import Patent
from .news_article import NewsArticle
from .relevance import RelevanceResult, VALID_CATEGORIES, normalize_category
from .extraction import ExtractionResult
from .entities import ResolvedEntity, AliasLink, create_resolved_entities, create_alias_links

__all__ = [
    "Patent",
    "NewsArticle",
    "RelevanceResult",
    "ExtractionResult",
    "ResolvedEntity",
    "AliasLink",
    "VALID_CATEGORIES",
    "normalize_category",
    "create_resolved_entities",
    "create_alias_links",
]


