# StudyOS

An AI-powered study assistant with a FastAPI backend and MongoDB (Atlas) storage.

## Features

- **Content Cruncher** — Upload a PDF, paste text, or enter a YouTube URL and generate summaries, flashcards, quizzes, and mind maps using Gemini AI.
- **Study Hub (Notebook)** — Create, organize, and edit rich-text notebooks stored in MongoDB GridFS.
- **Command Center** — Planner/calendar UI.
- **Dashboard** — Overview and quick access.

## Setup

1. **Install dependencies**

```bash
pip install -r requirements.txt
```

2. **Configure environment**

Edit `.env` and fill in your keys:

```
GEMINI_API_KEY=your_google_gemini_api_key      # Required for AI features
MONGODB_URI=your_mongodb_atlas_connection_string
```

Get a free Gemini API key at https://aistudio.google.com/app/apikey

3. **Run the server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Open the app**

Visit http://localhost:8000

## Deploying to Vercel

This project can be deployed to Vercel using the Python runtime. A `vercel.json` file is included and routes all requests to the FastAPI app in `app/main.py`.

Quick steps:

1. Install the Vercel CLI: `npm i -g vercel`
2. Login and link the project: `vercel login` then `vercel`
3. When prompted, select the project settings. Vercel will use `vercel.json` and `requirements.txt`.

Notes:

- Ensure environment variables (`GEMINI_API_KEY`, `MONGODB_URI`, etc.) are configured in the Vercel dashboard under the project Settings -> Environment Variables.
- Static files in `/static` and templates in `/templates` are bundled with the deployment and served by the function.
- The app is exposed by the serverless function; no `uvicorn` command is required on Vercel.

## Project Structure

```
StudyOS/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # MongoDB connection & GridFS
│   ├── ai_engine.py         # Gemini AI integration
│   ├── pdf_processor.py     # PDF text extraction
│   ├── youtube_parser.py    # YouTube transcript extraction
│   ├── routes/
│   │   ├── crunch.py        # /api/crunch/* — AI content processing
│   │   ├── notebook.py      # /api/notebook/* — Notebook CRUD
│   │   ├── auth.py          # /api/auth/*
│   │   └── files.py         # /api/files/*
│   ├── services/
│   │   ├── notebook_service.py
│   │   └── gridfs_service.py
│   └── models/ / utils/
├── templates/               # Jinja2 HTML templates
│   ├── index.html           # Dashboard
│   ├── cruncher.html        # Content Cruncher
│   ├── hub.html             # Study Hub
│   ├── notebook.html        # Notebook editor
│   └── command.html         # Command Center
└── .env                     # Environment variables (fill in your keys)
```
