# app/routes/history.py
"""Routes for Content Cruncher History — list, view, delete, export past results"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import io

router = APIRouter(prefix="/api/history", tags=["history"])

DEFAULT_USER_ID = "Skydrop"  # single-user app; swap for real auth user_id later


@router.get("")
async def list_history(
    user_id: str = Query(default=DEFAULT_USER_ID),
    source_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    """List Content Cruncher history entries, most recent first"""
    try:
        from app.database import get_history_service
        service = get_history_service()
        entries = await service.get_user_history(user_id, limit=limit, source_type=source_type)
        return {"status": "success", "data": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entry_id}")
async def get_history_entry(entry_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Get a single history entry with full result data"""
    try:
        from app.database import get_history_service
        service = get_history_service()
        entry = await service.get_entry(entry_id, user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="History entry not found.")
        return {"status": "success", "data": entry}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{entry_id}")
async def delete_history_entry(entry_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Delete a history entry"""
    try:
        from app.database import get_history_service
        service = get_history_service()
        deleted = await service.delete_entry(entry_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="History entry not found.")
        return {"status": "success", "message": "Deleted."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{entry_id}/export")
async def export_history_entry(entry_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Export a history entry's results as a styled .docx file"""
    try:
        from app.database import get_history_service
        from app.docx_exporter import build_export_docx

        service = get_history_service()
        entry = await service.get_entry(entry_id, user_id)
        if not entry:
            raise HTTPException(status_code=404, detail="History entry not found.")

        docx_bytes = build_export_docx(
            title="StudyOS Export",
            source_label=entry.get("sourceLabel", ""),
            source_type=entry.get("sourceType", "text"),
            result=entry.get("result", {}),
        )

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="studyos_export.docx"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
