# app/main.py
"""
StudySync AI Engine - Main FastAPI Application
Modular architecture with routes, services, and models
MongoDB with GridFS for file storage
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import uvicorn
from bson.objectid import ObjectId
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Import database and services
from app.database import (
    folders_collection,
    files_collection,
    get_grid_fs,
    get_gridfs_service,
    get_notebook_service,
    create_indexes
)

# Import routes
from app.routes import notebook, auth, files as files_routes

# =====================================================
# FastAPI Setup
# =====================================================

app = FastAPI(
    title="StudySync AI Engine",
    description="A MongoDB-based notebook system with file storage",
    version="1.0.0"
)

# =====================================================
# Setup Base Directories
# =====================================================

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Setup Jinja2 Templates
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# Setup Static Files
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# =====================================================
# Global Variables for Services
# =====================================================

grid_fs_service = None
notebook_service = None


async def init_services():
    """Initialize services on startup"""
    global grid_fs_service, notebook_service
    
    from app.services.gridfs_service import GridFSService
    from app.services.notebook_service import NotebookService
    
    grid_fs_service = GridFSService(get_grid_fs())
    notebook_service = NotebookService(
        folders_collection,
        files_collection,
        grid_fs_service
    )
    
    # Create database indexes
    try:
        await create_indexes()
        print("✅ Database indexes created")
    except Exception as e:
        print(f"⚠️  Index creation warning: {str(e)}")


# =====================================================
# Startup & Shutdown Events
# =====================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    print("🚀 Starting StudySync AI Engine...")
    await init_services()
    print("✅ Services initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("🛑 Shutting down StudySync AI Engine...")


# =====================================================
# Frontend Routes (HTML Templates)
# =====================================================

@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/cruncher", response_class=HTMLResponse)
async def read_cruncher(request: Request):
    """PDF Cruncher page"""
    return templates.TemplateResponse(request=request, name="cruncher.html")


@app.get("/hub", response_class=HTMLResponse)
async def read_hub(request: Request):
    """Hub/Dashboard page"""
    return templates.TemplateResponse(request=request, name="hub.html")


@app.get("/hub/notebook", response_class=HTMLResponse)
async def read_notebook(request: Request):
    """Notebook editor page"""
    return templates.TemplateResponse(request=request, name="notebook.html")


@app.get("/command", response_class=HTMLResponse)
async def read_command(request: Request):
    """Command center page"""
    return templates.TemplateResponse(request=request, name="command.html")


# =====================================================
# API Routes Registration
# =====================================================

# Register route modules
app.include_router(auth.router)
app.include_router(notebook.router)
app.include_router(files_routes.router)


# =====================================================
# Health Check Endpoint
# =====================================================

@app.get("/api/health")
async def health_check():
    """Check API health status"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "StudySync AI Engine"
    }


# =====================================================
# Root Info Endpoint
# =====================================================

@app.get("/api/info")
async def api_info():
    """Get API information"""
    return {
        "name": "StudySync AI Engine",
        "version": "1.0.0",
        "database": "MongoDB (MainProjectsDB)",
        "storage": "GridFS",
        "endpoints": {
            "auth": "/api/auth",
            "notebook": "/api/notebook",
            "files": "/api/files"
        }
    }


# =====================================================
# Error Handlers
# =====================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    print(f"❌ Unhandled exception: {str(exc)}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }


# =====================================================
# Development Server
# =====================================================

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
