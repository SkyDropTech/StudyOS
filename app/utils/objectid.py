# app/utils/objectid.py
"""ObjectId helper utilities"""

from bson import ObjectId
from typing import Any


def is_valid_objectid(id_string: str) -> bool:
    """Check if a string is a valid ObjectId"""
    try:
        ObjectId(id_string)
        return True
    except Exception:
        return False


def str_to_objectid(id_string: str) -> ObjectId:
    """Convert string to ObjectId with validation"""
    if not is_valid_objectid(id_string):
        raise ValueError(f"Invalid ObjectId: {id_string}")
    return ObjectId(id_string)
