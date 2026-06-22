# app/models/tasks.py
"""To-Do task data models"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class TaskCreate(BaseModel):
    """Payload for creating a new task"""
    title: str
    notes: Optional[str] = None
    priority: str = "medium"        # "low" | "medium" | "high"
    due_date: Optional[str] = None  # ISO date string e.g. "2026-06-25"
    tag: Optional[str] = None       # e.g. "Operating Systems"


class TaskUpdate(BaseModel):
    """Payload for updating an existing task (all fields optional)"""
    title: Optional[str] = None
    notes: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    tag: Optional[str] = None
    completed: Optional[bool] = None


class Task(BaseModel):
    """Full task model as stored / returned"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    title: str
    notes: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[str] = None
    tag: Optional[str] = None
    completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
