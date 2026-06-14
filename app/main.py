from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import uvicorn
from pathlib import Path

# Import custom modules
from app.youtube_parser import get_youtube_transcript
from app.ai_engine import generate_study_materials

# ==========================================
# INITIALIZE FASTAPI
# ==========================================
app = FastAPI(title="StudySync AI Engine")

# ==========================================
# FOLDER PATHS
# ==========================================
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# ==========================================
# PYDANTIC SCHEMAS
# ==========================================
class YouTubeRequest(BaseModel):
    url: str
    options: List[str]


class TextRequest(BaseModel):
    text: str
    options: List[str]


# ==========================================
# FRONTEND ROUTES
# ==========================================

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


@app.get("/command", response_class=HTMLResponse)
async def read_command(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="command.html",
    )


# ==========================================
# BACKEND API ROUTES
# ==========================================

@app.post("/api/crunch/youtube")
async def process_youtube(payload: YouTubeRequest):
    print(f"1. Received YouTube URL: {payload.url}")
    print(f"2. Requested Options: {payload.options}")

    # Get transcript
    transcript = get_youtube_transcript(payload.url)

    if transcript.startswith("Error"):
        return {
            "status": "error",
            "message": transcript
        }

    print("3. Transcript fetched successfully. Sending to Gemini AI...")

    # Generate study materials
    ai_results = generate_study_materials(
        transcript,
        payload.options
    )

    if "error" in ai_results:
        return {
            "status": "error",
            "message": ai_results["error"]
        }

    print("4. AI Processing Complete!")

    return {
        "status": "success",
        "message": "Content crunched successfully!",
        "data": ai_results,
    }


@app.post("/api/crunch/pdf")
async def process_pdf(
    file: UploadFile = File(...),
    options: str = Form(...)
):
    print(f"Received File: {file.filename}")

    return {
        "status": "success",
        "filename": file.filename,
        "options": options,
    }


# ==========================================
# RUN SERVER
# ==========================================

if __name__ == "__main__":
    print("Starting StudySync Server...")

    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )