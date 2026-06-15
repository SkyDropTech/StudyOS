# app/utils/serializer.py
"""Serialization utilities for MongoDB documents"""

from bson import ObjectId
from datetime import datetime
from typing import Any, Dict, List


def serialize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert MongoDB document to JSON-serializable format"""
    if not doc:
        return {}
    
    result = {}
    for key, value in doc.items():
        result[key] = serialize_value(value)
    return result


def serialize_value(value: Any) -> Any:
    """Convert individual values to JSON-serializable format"""
    if isinstance(value, ObjectId):
        return str(value)
    elif isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, dict):
        return {k: serialize_value(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [serialize_value(item) for item in value]
    else:
        return value


def serialize_documents(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert list of MongoDB documents to JSON-serializable format"""
    return [serialize_document(doc) for doc in docs]
