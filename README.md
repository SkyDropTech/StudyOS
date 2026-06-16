# StudyOS 🧠

![StudyOS Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**StudyOS** is an AI-powered, full-stack application designed to streamline information ingestion and study workflows. By leveraging automated parsing for multiple media formats and a modular AI engine, StudyOS transforms raw data into structured, interactive study materials.

---

## 🌟 Core Features

| Feature Domain | Description | Relevant Module(s) |
| :--- | :--- | :--- |
| **Multi-Modal Ingestion** | Parses and extracts raw text/data from PDFs and YouTube videos seamlessly. | `pdf_processor.py`[cite: 1], `youtube_parser.py`[cite: 1] |
| **AI Analysis Engine** | Summarizes, crunches, and formats complex data into digestible study guides. | `ai_engine.py`[cite: 1] |
| **Advanced File Storage** | Manages large, unstructured document uploads using scalable database architecture. | `gridfs_service.py`[cite: 1] |
| **Interactive Workspace** | Built-in user interfaces including a central Hub, Cruncher tool, and Notebooks. | `templates/*.html`[cite: 1] |
| **Secure Routing & Auth** | Manages user access, session security, and internal API routing. | `routes/auth.py`[cite: 1] |

---

## 🛠 Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend Framework** | Python (FastAPI / Flask) | Core application logic, RESTful API routing, and system architecture. |
| **Database Management** | MongoDB & GridFS | Handling structured user data alongside complex, large document storage. |
| **Frontend Rendering** | HTML5, CSS3, JavaScript | Server-side rendered interfaces delivering the user workspace. |
| **Deployment & CI/CD** | Vercel | Cloud hosting and continuous deployment pipelines (`vercel.json`)[cite: 1]. |

---

## 📂 Project Architecture

The repository is modularized to separate core business logic, API routing, and frontend views.

| Directory / File | Type | Description |
| :--- | :--- | :--- |
| `app/models/` | **Directory** | Contains database schemas and data models[cite: 1]. |
| `app/routes/` | **Directory** | API endpoint controllers (`auth.py`, `files.py`, `crunch.py`, `notebook.py`)[cite: 1]. |
| `app/services/` | **Directory** | Core business logic and database interactions (`notebook_service.py`)[cite: 1]. |
| `app/utils/` | **Directory** | Shared helper modules (`serializer.py`, `objectid.py`)[cite: 1]. |
| `app/ai_engine.py` | **Core Logic** | Orchestrates AI processing, parsing, and text generation[cite: 1]. |
| `app/pdf_processor.py` | **Data Parsing** | Handles extraction of text and metadata from PDF documents[cite: 1]. |
| `app/youtube_parser.py`| **Data Parsing** | Fetches and parses transcripts from YouTube URLs[cite: 1]. |
| `app/main.py` | **Entry Point** | Application initialization, middleware setup, and server config[cite: 1]. |
| `templates/` | **Directory** | User interface files (`hub.html`, `cruncher.html`, `notebook.html`)[cite: 1]. |
| `vercel.json` | **Config** | Vercel deployment routing and configuration specifications[cite: 1]. |

---

## 🚀 Installation & Setup

Follow these steps to get a local development environment running.

| Step | Action | Command / Details |
| :---: | :--- | :--- |
| **1** | **Clone Repository** | `git clone https://github.com/skydroptech/studyos.git`<br>`cd studyos` |
| **2** | **Virtual Environment**| `python -m venv venv`<br>**Mac/Linux:** `source venv/bin/activate`<br>**Windows:** `venv\Scripts\activate` |
| **3** | **Dependencies** | `pip install -r requirements.txt`[cite: 1] |
| **4** | **Configuration** | Create a `.env` file in the root directory. (See *Environment Variables* below). |
| **5** | **Run Application** | `python app/main.py`[cite: 1]<br>*Server will boot on localhost (typically port 8000).* |

### Environment Variables

Ensure the following variables are configured in your `.env` file prior to launching the application:

| Variable | Requirement | Description | Example |
| :--- | :---: | :--- | :--- |
| `MONGO_URI` | **Required** | Connection string for your local or cloud MongoDB database. | `mongodb://localhost:27017/studyos` |
| `SECRET_KEY` | **Required** | Cryptographic key for session and token security. | `your_super_secret_string` |
| `AI_API_KEY` | **Required** | API key for the core AI processing provider. | `sk-abc123def456...` |

---

## 📖 Project Documentation

For deeper technical insights, please refer to our internal documentation files:

| Resource | Description | Link |
| :--- | :--- | :--- |
| **API Documentation** | Complete endpoint references, request parameters, and payload schemas. | [`API_DOCUMENTATION.md`](./API_DOCUMENTATION.md)[cite: 1] |
| **Quick Start Guide** | Extended user setup and foundational operational guides. | [`QUICK_START.md`](./QUICK_START.md)[cite: 1] |
| **Restructure Notes** | Details on recent architectural shifts and code refactoring. | [`RESTRUCTURE_SUMMARY.md`](./RESTRUCTURE_SUMMARY.md)[cite: 1] |

---

## 🤝 Contributing & License

Contributions, issues, and feature requests are welcome! 

Distributed under the **MIT License**. See the [`LICENSE`](./LICENSE) file for more information[cite: 1].

**Maintainer:** [Your Name / skydroptech] - [your.email@example.com]
