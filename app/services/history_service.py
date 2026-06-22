# app/services/history_service.py
"""History service — saves and retrieves Content Cruncher results
(video / document / text -> summary / flashcards / quiz / mind map)
so users can revisit past generations later."""

from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from app.utils.serializer import serialize_document, serialize_documents


class HistoryService:
    """Service for managing Content Cruncher history entries"""

    def __init__(self, history_collection: AsyncIOMotorCollection):
        self.history_collection = history_collection

    async def save_entry(
        self,
        user_id: str,
        source_type: str,           # "video" | "document" | "text"
        source_label: str,          # YouTube URL, filename, or a snippet of pasted text
        options: List[str],         # ["Summary", "Flashcards", ...]
        result: dict,               # AI-generated data (summary/flashcards/quiz/mind_map)
    ) -> dict:
        """Save a new history entry"""
        now = datetime.utcnow()

        doc = {
            "userId": user_id,
            "sourceType": source_type,
            "sourceLabel": source_label,
            "options": options,
            "result": result,
            "createdAt": now,
        }

        inserted = await self.history_collection.insert_one(doc)
        doc["_id"] = inserted.inserted_id

        return serialize_document(doc)

    async def get_user_history(
        self,
        user_id: str,
        limit: int = 50,
        source_type: Optional[str] = None,
    ) -> List[dict]:
        """Get history entries for a user, most recent first"""
        query = {"userId": user_id}
        if source_type:
            query["sourceType"] = source_type

        cursor = self.history_collection.find(query).sort("createdAt", -1).limit(limit)
        entries = await cursor.to_list(None)
        return serialize_documents(entries)

    async def get_entry(self, entry_id: str, user_id: str) -> Optional[dict]:
        """Get a single history entry (with user verification)"""
        try:
            doc = await self.history_collection.find_one({
                "_id": ObjectId(entry_id),
                "userId": user_id,
            })
            return serialize_document(doc) if doc else None
        except Exception as e:
            raise Exception(f"Invalid history entry ID: {str(e)}")

    async def delete_entry(self, entry_id: str, user_id: str) -> bool:
        """Delete a history entry"""
        try:
            result = await self.history_collection.delete_one({
                "_id": ObjectId(entry_id),
                "userId": user_id,
            })
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Failed to delete history entry: {str(e)}")
