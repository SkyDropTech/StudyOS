# app/routes/crunch.py
"""Routes for the Content Cruncher - YouTube, PDF, and Text AI processing.
Every successful generation is saved to MongoDB history automatically."""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io
import json

router = APIRouter(prefix="/api/crunch", tags=["crunch"])

DEFAULT_USER_ID = "Skydrop"  # single-user app; swap for real auth user_id later


class YoutubeRequest(BaseModel):
    url: str
    options: List[str]


class TextRequest(BaseModel):
    text: str
    options: List[str]


class ExportRequest(BaseModel):
    source_label: str
    source_type: str
    result: dict


def _run_ai(content_text: str, options: List[str]) -> dict:
    """Run AI engine and return result dict"""
    from app.ai_engine import generate_study_materials
    return generate_study_materials(content_text, options)


async def _save_history(source_type: str, source_label: str, options: List[str], result: dict):
    """Best-effort save to MongoDB history. Never blocks the response on failure."""
    try:
        from app.database import get_history_service
        service = get_history_service()
        saved = await service.save_entry(
            user_id=DEFAULT_USER_ID,
            source_type=source_type,
            source_label=source_label,
            options=options,
            result=result,
        )
        return saved
    except Exception as e:
        print(f"⚠️  Failed to save history: {str(e)}")
        return None


@router.post("/youtube")
async def crunch_youtube(req: YoutubeRequest):
    """Extract YouTube transcript and generate study materials"""
    try:
        from app.youtube_parser import get_youtube_transcript
        transcript = get_youtube_transcript(req.url)
        if transcript.startswith("Error"):
            raise HTTPException(status_code=400, detail=transcript)

        result = _run_ai(transcript, req.options)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        saved = await _save_history("video", req.url, req.options, result)

        return {
            "status": "success",
            "data": result,
            "history_id": saved.get("_id") if saved else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pdf")
async def crunch_pdf(
    file: UploadFile = File(...),
    options: str = Form(...)
):
    """Extract text from PDF/TXT and generate study materials"""
    try:
        options_list: List[str] = json.loads(options)

        file_bytes = await file.read()

        if file.filename and file.filename.lower().endswith(".txt"):
            content_text = file_bytes.decode("utf-8", errors="ignore")
        else:
            # Treat as PDF
            from app.pdf_processor import extract_text_from_pdf
            content_text = extract_text_from_pdf(file_bytes)

        if not content_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from the uploaded file.")

        result = _run_ai(content_text, options_list)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        saved = await _save_history("document", file.filename or "document", options_list, result)

        return {
            "status": "success",
            "data": result,
            "history_id": saved.get("_id") if saved else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/text")
async def crunch_text(req: TextRequest):
    """Generate study materials from raw text"""
    try:
        if not req.text.strip():
            raise HTTPException(status_code=400, detail="Text content is empty.")

        result = _run_ai(req.text, req.options)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        label = req.text.strip()[:80] + ("..." if len(req.text.strip()) > 80 else "")
        saved = await _save_history("text", label, req.options, result)

        return {
            "status": "success",
            "data": result,
            "history_id": saved.get("_id") if saved else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export-docx")
async def export_docx(req: ExportRequest):
    """Export a freshly-generated result (not yet saved or already in view) as .docx"""
    try:
        from app.docx_exporter import build_export_docx

        docx_bytes = build_export_docx(
            title="StudyOS Export",
            source_label=req.source_label,
            source_type=req.source_type,
            result=req.result,
        )

        return StreamingResponse(
            io.BytesIO(docx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": 'attachment; filename="studyos_export.docx"'},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
