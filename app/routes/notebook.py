# app/routes/notebook.py
"""Routes for notebook operations"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from app.models.notebook import (
    NotebookFolder,
    NotebookFile,
    NotebookContent,
    NotebookUpdate
)

router = APIRouter(prefix="/api/notebook", tags=["notebook"])


async def get_notebook_service():
    """Dependency to get notebook service"""
    from app.services.notebook_service import NotebookService
    from app.database import folders_collection, files_collection, grid_fs_service
    
    return NotebookService(folders_collection, files_collection, grid_fs_service)


# ==================== FOLDER ENDPOINTS ====================

@router.post("/folders", response_model=dict)
async def create_folder(
    user_id: str,
    name: str,
    parent_id: Optional[str] = None,
    notebook_service = Depends(get_notebook_service)
):
    """Create a new folder for user"""
    try:
        folder = await notebook_service.create_folder(user_id, name, parent_id)
        return folder
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/folders", response_model=list)
async def get_user_folders(
    user_id: str,
    notebook_service = Depends(get_notebook_service)
):
    """Get all folders for a user"""
    try:
        folders = await notebook_service.get_user_folders(user_id)
        return folders
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/folders/{folder_id}", response_model=dict)
async def get_folder(
    folder_id: str,
    user_id: str,
    notebook_service = Depends(get_notebook_service)
):
    """Get a specific folder"""
    try:
        folder = await notebook_service.get_folder(folder_id, user_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        return folder
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/folders/{folder_id}", response_model=dict)
async def update_folder(
    folder_id: str,
    user_id: str,
    name: Optional[str] = None,
    parent_id: Optional[str] = None,
    notebook_service = Depends(get_notebook_service)
):
    """Update folder name"""
    try:
        folder = await notebook_service.update_folder(folder_id, user_id, name, parent_id)
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
        return folder
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/folders/{folder_id}", response_model=dict)
async def delete_folder(
    folder_id: str,
    user_id: str,
    notebook_service = Depends(get_notebook_service)
):
    """Delete a folder and all files in it"""
    try:
        success = await notebook_service.delete_folder(folder_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="Folder not found")
        return {"status": "success", "message": "Folder deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== FILE ENDPOINTS ====================

@router.post("/files", response_model=dict)
async def create_file(
    user_id: str,
    content: NotebookContent,
    notebook_service = Depends(get_notebook_service)
):
    """Create and upload a new notebook file"""
    try:
        file = await notebook_service.create_file(
            user_id,
            content.name,
            content.content,
            content.folder_id
        )
        return file
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files", response_model=list)
async def get_user_files(
    user_id: str,
    folder_id: Optional[str] = None,
    notebook_service = Depends(get_notebook_service)
):
    """Get all files for a user"""
    try:
        files = await notebook_service.get_user_files(user_id, folder_id)
        return files
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/{file_id}", response_model=dict)
async def get_file(
    file_id: str,
    user_id: str,
    notebook_service = Depends(get_notebook_service)
):
    """Get file metadata"""
    try:
        file = await notebook_service.get_file(file_id, user_id)
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return file
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/files/{file_id}/content")
async def get_file_content(
    file_id: str,
    user_id: str,
    notebook_service = Depends(get_notebook_service)
):
    """Get full file content"""
    try:
        content = await notebook_service.get_file_content(file_id, user_id)
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/files/{file_id}", response_model=dict)
async def update_file(
    file_id: str,
    user_id: str,
    update: NotebookUpdate,
    notebook_service = Depends(get_notebook_service)
):
    """Update file content and/or name"""
    try:
        file = await notebook_service.update_file(
                file_id,
                user_id,
                update.name,
                update.content,
                update.folder_id
        )
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return file
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/files/{file_id}", response_model=dict)
async def delete_file(
    file_id: str,
    user_id: str,
    notebook_service = Depends(get_notebook_service)
):
    """Delete a file"""
    try:
        success = await notebook_service.delete_file(file_id, user_id)
        if not success:
            raise HTTPException(status_code=404, detail="File not found")
        return {"status": "success", "message": "File deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
async def search_files(
    user_id: str,
    query: str,
    notebook_service = Depends(get_notebook_service)
):
    """Search files by name"""
    try:
        if not query or len(query) < 2:
            raise HTTPException(status_code=400, detail="Query too short")
        
        files = await notebook_service.search_files(user_id, query)
        return files
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
