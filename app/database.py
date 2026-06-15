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
    "mongodb+srv://rishikeshtechofficial_db_user:ZxxHeBTkx8ZWKzxz@mainprojectsdb.cby2tqt.mongodb.net/?appName=MainProjectsDB"
)

try:
    # Connect to MongoDB Atlas
    client = AsyncIOMotorClient(MONGODB_URI)
    
    # Use the specific database from your cluster
    db = client.get_database("MainProjectsDB")
    
    # ===== METADATA COLLECTIONS =====
    # These collections store metadata about folders and files
    folders_collection = db.folders
    files_collection = db.files
    
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
    
    print("✅ Successfully connected to MongoDB Atlas")
    print("   Database: MainProjectsDB")
    print("   Collections: folders, files")
    print("   GridFS: fs.files, fs.chunks (lazy-initialized)")
    print("   📁 User data structure:")
    print("      └─ userId (e.g., 'Skydrop')")
    print("         ├─ Projects (folder)")
    print("         │  └─ architecture.png (file in GridFS)")
    print("         ├─ Work (folder)")
    print("         └─ Docs (folder)")
    
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


# Make services accessible
grid_fs_service = None  # Will be initialized on demand


__all__ = [
    "client",
    "db",
    "folders_collection",
    "files_collection",
    "get_grid_fs",
    "grid_fs_service",
    "get_gridfs_service",
    "get_notebook_service",
    "create_indexes"
]