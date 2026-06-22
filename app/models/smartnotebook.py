# app/models/smartnotebook.py
"""Smart Notebook data models.

A Smart Notebook is a user-created, color/icon-customized "binder" that can hold
folders and items of ANY kind: notes, PDFs, slide decks, video links, or any
other uploaded file — everything saved together in one place.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId


# ---------- Notebook (the binder itself) ----------

class NotebookCreate(BaseModel):
    title: str
    icon: str = "fa-solid fa-book"       # font-awesome class
    color: str = "#6D5EF7"               # hex accent color
    description: Optional[str] = None


class NotebookUpdateMeta(BaseModel):
    title: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    description: Optional[str] = None


# ---------- Folder (organizes items within a notebook) ----------

class NBFolderCreate(BaseModel):
    name: str
    parent_id: Optional[str] = None


class NBFolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None  # "" to move to root


# ---------- Item (a file / link / note inside a notebook) ----------
# item_type: "note" | "link" | "file"
#   note -> text content stored inline (Mongo doc)
#   link -> external URL (e.g. YouTube video, article) stored inline
#   file -> binary content stored in GridFS (PDF, PPTX, DOCX, image, etc.)

class NBItemCreateNote(BaseModel):
    name: str
    content: str = ""
    folder_id: Optional[str] = None


class NBItemCreateLink(BaseModel):
    name: str
    url: str
    folder_id: Optional[str] = None
    link_kind: str = "video"  # "video" | "article" | "other"


class NBItemUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None   # for notes
    url: Optional[str] = None       # for links
    folder_id: Optional[str] = None  # "" to move to root
