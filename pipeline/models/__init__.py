from .patent import Patent
from .news_article import NewsArticle
from .relevance import RelevanceResult, VALID_CATEGORIES, normalize_category

__all__ = [
    "Patent",
    "NewsArticle",
    "RelevanceResult",
    "VALID_CATEGORIES",
    "normalize_category",
]


