# app/models/notebook.py
"""Notebook data models"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


class NotebookFolder(BaseModel):
    """Folder model for organizing notebooks"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    name: str
    parent_id: Optional[str] = None
    path: str = "/"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class NotebookFile(BaseModel):
    """File/Notebook model for storing notebook content"""
    id: Optional[str] = Field(None, alias="_id")
    user_id: str
    name: str
    folder_id: Optional[str] = None
    size: int = 0
    mime_type: str = "text/html"
    grid_fs_file_id: str  # Reference to GridFS file
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}


class NotebookContent(BaseModel):
    """Notebook content model for uploads"""
    name: str
    content: str  # HTML content from notebook.html
    folder_id: Optional[str] = None


class NotebookUpdate(BaseModel):
    """Model for updating notebook files"""
    name: Optional[str] = None
    content: Optional[str] = None
    folder_id: Optional[str] = None
