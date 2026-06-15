# app/routes/crunch.py
"""Routes for the Content Cruncher - YouTube, PDF, and Text AI processing"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import json

router = APIRouter(prefix="/api/crunch", tags=["crunch"])


class YoutubeRequest(BaseModel):
    url: str
    options: List[str]


class TextRequest(BaseModel):
    text: str
    options: List[str]


def _run_ai(content_text: str, options: List[str]) -> dict:
    """Run AI engine and return result dict"""
    from app.ai_engine import generate_study_materials
    return generate_study_materials(content_text, options)


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

        return {"status": "success", "data": result}
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

        return {"status": "success", "data": result}
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

        return {"status": "success", "data": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
