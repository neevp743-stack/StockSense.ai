"""
StockSense AI — News Data Validator
Validates article data for schema integrity and publication timestamp sanity.
"""

from typing import Dict, Any
from datetime import datetime

def validate_news_article(article: Dict[str, Any]) -> Dict[str, Any]:
    errors = []
    if not article.get("article_id"):
        errors.append("Missing article_id")
    if not article.get("symbol"):
        errors.append("Missing symbol")
    if not article.get("headline"):
        errors.append("Missing headline")
    if not article.get("published_timestamp"):
        errors.append("Missing published_timestamp")

    pub_ts = article.get("published_timestamp")
    if isinstance(pub_ts, datetime) and pub_ts > datetime.utcnow():
        errors.append("Publication timestamp is in the future")

    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    }
