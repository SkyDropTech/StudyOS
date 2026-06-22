# app/services/tasks_service.py
"""Tasks service — CRUD for the daily To-Do list, stored in MongoDB"""

from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from app.utils.serializer import serialize_document, serialize_documents


class TasksService:
    """Service for managing a user's To-Do tasks"""

    def __init__(self, tasks_collection: AsyncIOMotorCollection):
        self.tasks_collection = tasks_collection

    async def create_task(
        self,
        user_id: str,
        title: str,
        notes: Optional[str] = None,
        priority: str = "medium",
        due_date: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> dict:
        """Create a new task for the user"""
        now = datetime.utcnow()

        doc = {
            "userId": user_id,
            "title": title,
            "notes": notes,
            "priority": priority if priority in ("low", "medium", "high") else "medium",
            "dueDate": due_date,
            "tag": tag,
            "completed": False,
            "createdAt": now,
            "updatedAt": now,
        }

        result = await self.tasks_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_document(doc)

    async def get_user_tasks(
        self,
        user_id: str,
        completed: Optional[bool] = None,
    ) -> List[dict]:
        """Get all tasks for a user, optionally filtered by completion status.
        Sorted: incomplete first, then by due date (soonest first), then newest created."""
        query = {"userId": user_id}
        if completed is not None:
            query["completed"] = completed

        cursor = self.tasks_collection.find(query).sort([
            ("completed", 1),
            ("createdAt", -1),
        ])
        tasks = await cursor.to_list(None)
        return serialize_documents(tasks)

    async def get_task(self, task_id: str, user_id: str) -> Optional[dict]:
        """Get a single task (with user verification)"""
        try:
            doc = await self.tasks_collection.find_one({
                "_id": ObjectId(task_id),
                "userId": user_id,
            })
            return serialize_document(doc) if doc else None
        except Exception as e:
            raise Exception(f"Invalid task ID: {str(e)}")

    async def update_task(
        self,
        task_id: str,
        user_id: str,
        title: Optional[str] = None,
        notes: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        tag: Optional[str] = None,
        completed: Optional[bool] = None,
    ) -> Optional[dict]:
        """Update an existing task. Only provided fields are changed."""
        try:
            update_data = {"updatedAt": datetime.utcnow()}

            if title is not None:
                update_data["title"] = title
            if notes is not None:
                update_data["notes"] = notes
            if priority is not None and priority in ("low", "medium", "high"):
                update_data["priority"] = priority
            if due_date is not None:
                update_data["dueDate"] = due_date if due_date != "" else None
            if tag is not None:
                update_data["tag"] = tag if tag != "" else None
            if completed is not None:
                update_data["completed"] = completed

            updated = await self.tasks_collection.find_one_and_update(
                {"_id": ObjectId(task_id), "userId": user_id},
                {"$set": update_data},
                return_document=True,
            )
            return serialize_document(updated) if updated else None
        except Exception as e:
            raise Exception(f"Failed to update task: {str(e)}")

    async def toggle_task(self, task_id: str, user_id: str) -> Optional[dict]:
        """Flip the completed status of a task"""
        task = await self.get_task(task_id, user_id)
        if not task:
            return None
        return await self.update_task(task_id, user_id, completed=not task.get("completed", False))

    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete a task"""
        try:
            result = await self.tasks_collection.delete_one({
                "_id": ObjectId(task_id),
                "userId": user_id,
            })
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Failed to delete task: {str(e)}")

    async def get_stats(self, user_id: str) -> dict:
        """Get quick stats for the dashboard widget"""
        total = await self.tasks_collection.count_documents({"userId": user_id})
        completed = await self.tasks_collection.count_documents({"userId": user_id, "completed": True})
        pending = total - completed
        return {"total": total, "completed": completed, "pending": pending}
