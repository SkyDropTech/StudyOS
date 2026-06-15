# app/main.py

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from bson.objectid import ObjectId
from fastapi import (
    FastAPI,
    Request,
    HTTPException,
)
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Import DB connection
from app.database import notebook_collection

# Import custom modules
from app.youtube_parser import get_youtube_transcript
from app.pdf_processor import extract_text_from_pdf
from app.ai_engine import generate_study_materials

app = FastAPI(title="StudySync AI Engine")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


# =====================================================
# Notebook Schemas
# =====================================================

class NotebookItem(BaseModel):
    type: str  # "folder" or "file"
    name: str
    parent_id: Optional[str] = None
    content: str = ""
    user_id: str = "default_user"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NotebookItemUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None


# =====================================================
# Frontend Routes
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/cruncher", response_class=HTMLResponse)
async def read_cruncher(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="cruncher.html",
    )


@app.get("/hub", response_class=HTMLResponse)
async def read_hub(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="hub.html",
    )


@app.get("/hub/notebook", response_class=HTMLResponse)
async def read_notebook(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="notebook.html",
    )


@app.get("/command", response_class=HTMLResponse)
async def read_command(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="command.html",
    )


# =====================================================
# Notebook API Routes
# =====================================================

@app.post("/api/notebook/items")
async def create_item(item: NotebookItem):
    result = await notebook_collection.insert_one(item.model_dump())

    return {
        "status": "success",
        "id": str(result.inserted_id),
    }


@app.get("/api/notebook/items/{user_id}")
async def get_items(user_id: str):
    cursor = notebook_collection.find({"user_id": user_id})
    items = await cursor.to_list(length=1000)

    for item in items:
        item["_id"] = str(item["_id"])

    return {
        "status": "success",
        "items": items,
    }


@app.put("/api/notebook/items/{item_id}")
async def update_item(
    item_id: str,
    update_data: NotebookItemUpdate,
):
    update_fields = {}

    if update_data.name is not None:
        update_fields["name"] = update_data.name

    if update_data.content is not None:
        update_fields["content"] = update_data.content

    try:
        await notebook_collection.update_one(
            {"_id": ObjectId(item_id)},
            {"$set": update_fields},
        )

        return {
            "status": "success",
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="DB Error",
        )


@app.delete("/api/notebook/items/{item_id}")
async def delete_item(item_id: str):
    try:
        await notebook_collection.delete_one(
            {"_id": ObjectId(item_id)}
        )

        # Delete all children if the item is a folder
        await notebook_collection.delete_many(
            {"parent_id": item_id}
        )

        return {
            "status": "success",
        }

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="DB Error",
        )


# =====================================================
# Run Server
# =====================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )