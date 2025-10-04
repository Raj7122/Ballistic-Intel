from .patent import Patent
from .news_article import NewsArticle
from .relevance import RelevanceResult, VALID_CATEGORIES, normalize_category
from .extraction import ExtractionResult

__all__ = [
    "Patent",
    "NewsArticle",
    "RelevanceResult",
    "ExtractionResult",
    "VALID_CATEGORIES",
    "normalize_category",
]


