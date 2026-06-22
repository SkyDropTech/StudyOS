# app/database.py
"""
MongoDB database configuration with GridFS for StudyOS
User data is organized by user_id, with:
- folders collection: stores folder metadata
- files collection: stores file/notebook metadata  
- GridFS: stores actual file content (chunks & files collections)
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from dotenv import load_dotenv

load_dotenv()

# MongoDB Connection
MONGODB_URI = os.getenv(
    "MONGODB_URI",
    "mongodb+srv://Skydrop:Skydrop123@booklibrary.gpib5sv.mongodb.net/focusdesk?retryWrites=true&w=majority&appName=BookLibrary"
)

try:
    # Connect to MongoDB Atlas
    client = AsyncIOMotorClient(MONGODB_URI)
    
    # Use the specific database from your cluster
    db = client.get_database("focusdesk")
    
    # ===== METADATA COLLECTIONS =====
    # These collections store metadata about folders and files
    folders_collection = db.folders
    files_collection = db.files
    history_collection = db.history  # Content Cruncher history (video/doc/text -> results)
    tasks_collection = db.tasks  # To-Do list tasks
    notebooks_collection = db.notebooks  # Smart Notebooks (title, color, icon)
    nb_folders_collection = db.notebook_folders  # Folders inside a Smart Notebook
    nb_items_collection = db.notebook_items  # Items (files/links/notes) inside a Smart Notebook
    
    # ===== GRIDFS BUCKET =====
    # GridFS stores the actual file content (binary data)
    # Initialize lazily to avoid event loop issues during import
    _grid_fs_instance = None
    
    def get_grid_fs():
        """Get or create GridFS instance"""
        global _grid_fs_instance
        if _grid_fs_instance is None:
            _grid_fs_instance = AsyncIOMotorGridFSBucket(db)
        return _grid_fs_instance
    
    # For backward compatibility
    grid_fs = None  # Will be set during initialization
    
    # ===== CREATE INDEXES FOR BETTER PERFORMANCE =====
    async def create_indexes():
        """Create indexes for better query performance"""
        # Index for quick user lookups in folders
        await folders_collection.create_index("userId")
        await folders_collection.create_index([("userId", 1), ("parentId", 1)])
        
        # Index for quick user lookups in files
        await files_collection.create_index("userId")
        await files_collection.create_index([("userId", 1), ("folderId", 1)])
        await files_collection.create_index("name")  # For search functionality

        # Index for history (Content Cruncher results)
        await history_collection.create_index("userId")
        await history_collection.create_index([("userId", 1), ("createdAt", -1)])
        await history_collection.create_index([("userId", 1), ("sourceType", 1)])

        # Index for to-do tasks
        await tasks_collection.create_index("userId")
        await tasks_collection.create_index([("userId", 1), ("completed", 1)])
        await tasks_collection.create_index([("userId", 1), ("dueDate", 1)])

        # Index for Smart Notebooks
        await notebooks_collection.create_index("userId")
        await nb_folders_collection.create_index([("userId", 1), ("notebookId", 1)])
        await nb_items_collection.create_index([("userId", 1), ("notebookId", 1)])
        await nb_items_collection.create_index([("userId", 1), ("notebookId", 1), ("folderId", 1)])
    
    print("✅ Successfully connected to MongoDB Atlas")
    print("   Database: focusdesk")
    print("   Collections: folders, files, history, tasks, notebooks, notebook_folders, notebook_items")
    print("   GridFS: fs.files, fs.chunks (lazy-initialized)")
    
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {str(e)}")
    raise e

# ===== SERVICE INITIALIZATION =====
# Import and initialize services here to avoid circular imports
_gridfs_service = None
_notebook_service = None


def get_gridfs_service():
    """Get GridFS service instance"""
    global _gridfs_service
    if _gridfs_service is None:
        from app.services.gridfs_service import GridFSService
        _gridfs_service = GridFSService(get_grid_fs())
    return _gridfs_service


def get_notebook_service():
    """Get Notebook service instance"""
    global _notebook_service
    if _notebook_service is None:
        from app.services.notebook_service import NotebookService
        _notebook_service = NotebookService(
            folders_collection,
            files_collection,
            get_gridfs_service()
        )
    return _notebook_service


_history_service = None


def get_history_service():
    """Get History service instance"""
    global _history_service
    if _history_service is None:
        from app.services.history_service import HistoryService
        _history_service = HistoryService(history_collection)
    return _history_service


_tasks_service = None


def get_tasks_service():
    """Get Tasks (To-Do) service instance"""
    global _tasks_service
    if _tasks_service is None:
        from app.services.tasks_service import TasksService
        _tasks_service = TasksService(tasks_collection)
    return _tasks_service


_smart_notebook_service = None


def get_smart_notebook_service():
    """Get Smart Notebook service instance (folders/files/links inside a notebook)"""
    global _smart_notebook_service
    if _smart_notebook_service is None:
        from app.services.smartnotebook_service import SmartNotebookService
        _smart_notebook_service = SmartNotebookService(
            notebooks_collection,
            nb_folders_collection,
            nb_items_collection,
            get_gridfs_service()
        )
    return _smart_notebook_service


# Make services accessible
grid_fs_service = None  # Will be initialized on demand


__all__ = [
    "client",
    "db",
    "folders_collection",
    "files_collection",
    "history_collection",
    "tasks_collection",
    "notebooks_collection",
    "nb_folders_collection",
    "nb_items_collection",
    "get_grid_fs",
    "grid_fs_service",
    "get_gridfs_service",
    "get_notebook_service",
    "get_history_service",
    "get_tasks_service",
    "get_smart_notebook_service",
    "create_indexes"
]