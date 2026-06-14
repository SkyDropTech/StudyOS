from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List
import uvicorn
import os  # <-- Added this

# Initialize FastAPI App
app = FastAPI(title="StudySync AI Engine")

# ==========================================
# BULLETPROOF FOLDER PATHING
# ==========================================
# This automatically finds the root StudyOS folder and points to 'templates'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")

# Mount templates using the absolute path
templates = Jinja2Templates(directory=TEMPLATE_DIR)

# --- PYDANTIC SCHEMAS (Data Validation) ---
class YouTubeRequest(BaseModel):
    url: str
    options: List[str]

class TextRequest(BaseModel):
    text: str
    options: List[str]

# ==========================================
# 1. FRONTEND ROUTES 
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/cruncher", response_class=HTMLResponse)
async def read_cruncher(request: Request):
    return templates.TemplateResponse("cruncher.html", {"request": request})

@app.get("/hub", response_class=HTMLResponse)
async def read_hub(request: Request):
    return templates.TemplateResponse("hub.html", {"request": request})

@app.get("/command", response_class=HTMLResponse)
async def read_command(request: Request):
    return templates.TemplateResponse("command.html", {"request": request})

# ==========================================
# 2. BACKEND API ROUTES 
# ==========================================

@app.post("/api/crunch/youtube")
async def process_youtube(payload: YouTubeRequest):
    """ Receives JSON: {"url": "https...", "options": ["summary", "flashcards"]} """
    print(f"Received YouTube URL: {payload.url}")
    print(f"Requested Options: {payload.options}")
    return {"status": "success", "message": "YouTube processed", "data": payload.model_dump()}

@app.post("/api/crunch/pdf")
async def process_pdf(file: UploadFile = File(...), options: str = Form(...)):
    """Note: FastAPI file uploads require python-multipart to be installed."""
    print(f"Received File: {file.filename}")
    return {"status": "success", "filename": file.filename, "options": options}

if __name__ == "__main__":
    print("Starting StudySync Server...")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)