# app/routes/smartnotebook.py
"""Routes for Smart Notebooks — the unified binder where users can save
folders, notes, video/article links, and any uploaded file (PDF, PPTX, DOCX,
images, etc.) all in one organized place."""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional
import io

from app.models.smartnotebook import (
    NotebookCreate,
    NotebookUpdateMeta,
    NBFolderCreate,
    NBFolderUpdate,
    NBItemCreateNote,
    NBItemCreateLink,
    NBItemUpdate,
)

router = APIRouter(prefix="/api/smartnotebook", tags=["smartnotebook"])

DEFAULT_USER_ID = "Skydrop"


def _service():
    from app.database import get_smart_notebook_service
    return get_smart_notebook_service()


# ==================== NOTEBOOKS ====================

@router.post("/notebooks")
async def create_notebook(payload: NotebookCreate, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        if not payload.title or not payload.title.strip():
            raise HTTPException(status_code=400, detail="Title is required")
        nb = await _service().create_notebook(
            user_id, payload.title.strip(), payload.icon, payload.color, payload.description
        )
        return {"status": "success", "data": nb}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notebooks")
async def list_notebooks(user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        notebooks = await _service().get_user_notebooks(user_id)
        return {"status": "success", "data": notebooks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notebooks/{notebook_id}")
async def get_notebook(notebook_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        nb = await _service().get_notebook(notebook_id, user_id)
        if not nb:
            raise HTTPException(status_code=404, detail="Notebook not found")
        return {"status": "success", "data": nb}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/notebooks/{notebook_id}")
async def update_notebook(notebook_id: str, payload: NotebookUpdateMeta, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        nb = await _service().update_notebook(
            notebook_id, user_id, payload.title, payload.icon, payload.color, payload.description
        )
        if not nb:
            raise HTTPException(status_code=404, detail="Notebook not found")
        return {"status": "success", "data": nb}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/notebooks/{notebook_id}")
async def delete_notebook(notebook_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        deleted = await _service().delete_notebook(notebook_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Notebook not found")
        return {"status": "success", "message": "Notebook deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== FOLDERS ====================

@router.post("/notebooks/{notebook_id}/folders")
async def create_folder(notebook_id: str, payload: NBFolderCreate, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        folder = await _service().create_folder(notebook_id, user_id, payload.name, payload.parent_id)
        return {"status": "success", "data": folder}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notebooks/{notebook_id}/folders")
async def list_folders(notebook_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        folders = await _service().get_folders(notebook_id, user_id)
        return {"status": "success", "data": folders}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/folders/{folder_id}")
async def update_folder(folder_id: str, payload: NBFolderUpdate, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        folder = await _service().update_folder(folder_id, user_id, payload.name, payload.parent_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"status": "success", "data": folder}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/folders/{folder_id}")
async def delete_folder(folder_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        deleted = await _service().delete_folder(folder_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"status": "success", "message": "Folder deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== ITEMS (notes / links / files) ====================

@router.get("/notebooks/{notebook_id}/items")
async def list_items(notebook_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        items = await _service().get_items(notebook_id, user_id)
        return {"status": "success", "data": items}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notebooks/{notebook_id}/items/note")
async def create_note(notebook_id: str, payload: NBItemCreateNote, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        item = await _service().create_note(
            notebook_id, user_id, payload.name, payload.content, payload.folder_id
        )
        return {"status": "success", "data": item}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notebooks/{notebook_id}/items/link")
async def create_link(notebook_id: str, payload: NBItemCreateLink, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        if not payload.url or not payload.url.strip():
            raise HTTPException(status_code=400, detail="URL is required")
        item = await _service().create_link(
            notebook_id, user_id, payload.name, payload.url.strip(), payload.link_kind, payload.folder_id
        )
        return {"status": "success", "data": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/notebooks/{notebook_id}/items/file")
async def upload_file_item(
    notebook_id: str,
    file: UploadFile = File(...),
    folder_id: Optional[str] = Form(default=None),
    user_id: str = Query(default=DEFAULT_USER_ID),
):
    """Upload ANY file type (PDF, PPTX, DOCX, images, etc.) into a notebook"""
    try:
        data = await file.read()
        if len(data) > 25 * 1024 * 1024:  # 25MB cap
            raise HTTPException(status_code=400, detail="File too large (max 25MB)")
        item = await _service().create_file(
            notebook_id,
            user_id,
            file.filename or "Untitled",
            data,
            file.content_type or "application/octet-stream",
            folder_id if folder_id else None,
        )
        return {"status": "success", "data": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/items/{item_id}")
async def get_item(item_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        item = await _service().get_item(item_id, user_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "success", "data": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/items/{item_id}/download")
async def download_item(item_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Stream a file item's binary content back (for preview or download)"""
    try:
        data, filename, content_type = await _service().get_file_bytes(item_id, user_id)
        return StreamingResponse(
            io.BytesIO(data),
            media_type=content_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/items/{item_id}")
async def update_item(item_id: str, payload: NBItemUpdate, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        item = await _service().update_item(
            item_id, user_id, payload.name, payload.content, payload.url, payload.folder_id
        )
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "success", "data": item}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/items/{item_id}")
async def delete_item(item_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        deleted = await _service().delete_item(item_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"status": "success", "message": "Item deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/notebooks/{notebook_id}/search")
async def search_items(notebook_id: str, query: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    try:
        if not query or len(query) < 1:
            raise HTTPException(status_code=400, detail="Query required")
        items = await _service().search(notebook_id, user_id, query)
        return {"status": "success", "data": items}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
