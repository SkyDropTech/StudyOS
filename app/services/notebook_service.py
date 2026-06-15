# app/services/notebook_service.py
"""Notebook service for managing notebook operations"""

from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from app.utils.serializer import serialize_document, serialize_documents


class NotebookService:
    """Service for managing notebook folders and files"""
    
    def __init__(
        self,
        folders_collection: AsyncIOMotorCollection,
        files_collection: AsyncIOMotorCollection,
        gridfs_service
    ):
        self.folders_collection = folders_collection
        self.files_collection = files_collection
        self.gridfs_service = gridfs_service
    
    # ==================== FOLDER OPERATIONS ====================
    
    async def create_folder(
        self,
        user_id: str,
        name: str,
        parent_id: Optional[str] = None
    ) -> dict:
        """Create a new folder for user"""
        now = datetime.utcnow()
        
        folder_doc = {
            "userId": user_id,
            "name": name,
            "parentId": ObjectId(parent_id) if parent_id else None,
            "path": "/",
            "createdAt": now,
            "updatedAt": now
        }
        
        result = await self.folders_collection.insert_one(folder_doc)
        folder_doc["_id"] = result.inserted_id
        
        return serialize_document(folder_doc)
    
    async def get_user_folders(self, user_id: str) -> List[dict]:
        """Get all folders for a user"""
        folders = await self.folders_collection.find({
            "userId": user_id
        }).to_list(None)
        
        return serialize_documents(folders)
    
    async def get_folder(self, folder_id: str, user_id: str) -> Optional[dict]:
        """Get a specific folder (with user verification)"""
        try:
            folder = await self.folders_collection.find_one({
                "_id": ObjectId(folder_id),
                "userId": user_id
            })
            return serialize_document(folder) if folder else None
        except Exception as e:
            raise Exception(f"Invalid folder ID: {str(e)}")
    
    async def update_folder(
        self,
        folder_id: str,
        user_id: str,
        name: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> Optional[dict]:
        """Update folder name"""
        try:
            update_data = {"updatedAt": datetime.utcnow()}
            
            if name:
                update_data["name"] = name
            
            if parent_id is not None:
                try:
                    update_data["parentId"] = None if parent_id == "" else ObjectId(parent_id)
                except Exception:
                    raise Exception(f"Invalid parent folder ID: {parent_id}")
            
            updated_folder = await self.folders_collection.find_one_and_update(
                {"_id": ObjectId(folder_id), "userId": user_id},
                {"$set": update_data},
                return_document=True
            )
            
            return serialize_document(updated_folder) if updated_folder else None
        except Exception as e:
            raise Exception(f"Failed to update folder: {str(e)}")
    
    async def delete_folder(self, folder_id: str, user_id: str) -> bool:
        """Delete a folder (and associated files)"""
        try:
            # Delete all files in folder
            files_to_delete = await self.files_collection.find({
                "folderId": ObjectId(folder_id),
                "userId": user_id
            }).to_list(None)
            
            for file_doc in files_to_delete:
                await self.gridfs_service.delete_file(str(file_doc["gridFsFileId"]))
                await self.files_collection.delete_one({"_id": file_doc["_id"]})
            
            # Delete folder
            result = await self.folders_collection.delete_one({
                "_id": ObjectId(folder_id),
                "userId": user_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Failed to delete folder: {str(e)}")
    
    # ==================== FILE OPERATIONS ====================
    
    async def create_file(
        self,
        user_id: str,
        name: str,
        content: str,
        folder_id: Optional[str] = None
    ) -> dict:
        """Create a new notebook file"""
        try:
            now = datetime.utcnow()
            
            # Upload content to GridFS
            grid_fs_id = await self.gridfs_service.upload_file(
                name, content, user_id, folder_id
            )
            
            # Create metadata in files collection
            file_doc = {
                "userId": user_id,
                "name": name,
                "folderId": ObjectId(folder_id) if folder_id else None,
                "size": len(content.encode('utf-8')),
                "mimeType": "text/html",
                "gridFsFileId": ObjectId(grid_fs_id),
                "createdAt": now,
                "updatedAt": now
            }
            
            result = await self.files_collection.insert_one(file_doc)
            file_doc["_id"] = result.inserted_id
            
            return serialize_document(file_doc)
        except Exception as e:
            raise Exception(f"Failed to create file: {str(e)}")
    
    async def get_user_files(
        self,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> List[dict]:
        """Get all files for a user (optionally filtered by folder)"""
        # Build query to fetch files. If folder_id is provided, filter by it.
        query = {"userId": user_id}

        if folder_id is not None:
            try:
                query["folderId"] = ObjectId(folder_id)
            except Exception:
                raise Exception(f"Invalid folder ID: {folder_id}")

        # If folder_id is omitted (None), do not filter by folder so we return all user files
        files = await self.files_collection.find(query).to_list(None)
        return serialize_documents(files)
    
    async def get_file(self, file_id: str, user_id: str) -> Optional[dict]:
        """Get a specific file metadata (with user verification)"""
        try:
            file_doc = await self.files_collection.find_one({
                "_id": ObjectId(file_id),
                "userId": user_id
            })
            return serialize_document(file_doc) if file_doc else None
        except Exception as e:
            raise Exception(f"Invalid file ID: {str(e)}")
    
    async def get_file_content(self, file_id: str, user_id: str) -> str:
        """Get the full content of a file"""
        try:
            file_doc = await self.files_collection.find_one({
                "_id": ObjectId(file_id),
                "userId": user_id
            })
            
            if not file_doc:
                raise Exception("File not found")
            
            grid_fs_id = str(file_doc["gridFsFileId"])
            content = await self.gridfs_service.download_file(grid_fs_id)
            
            return content
        except Exception as e:
            raise Exception(f"Failed to get file content: {str(e)}")
    
    async def update_file(
        self,
        file_id: str,
        user_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        folder_id: Optional[str] = None
    ) -> Optional[dict]:
        """Update file name and/or content"""
        try:
            file_doc = await self.files_collection.find_one({
                "_id": ObjectId(file_id),
                "userId": user_id
            })
            
            if not file_doc:
                raise Exception("File not found")
            
            # Update content in GridFS if provided
            if content:
                new_grid_fs_id = await self.gridfs_service.update_file(
                    str(file_doc["gridFsFileId"]),
                    content
                )
                file_doc["gridFsFileId"] = ObjectId(new_grid_fs_id)
            
            # Update metadata
            update_data = {
                "updatedAt": datetime.utcnow(),
                "gridFsFileId": file_doc.get("gridFsFileId", file_doc["gridFsFileId"])
            }
            
            if name:
                update_data["name"] = name
            
            if content:
                update_data["size"] = len(content.encode('utf-8'))
            
            if folder_id is not None:
                # Allow moving file to another folder (folder_id may be empty string to indicate root)
                try:
                    update_data["folderId"] = None if folder_id == "" else ObjectId(folder_id)
                except Exception:
                    raise Exception(f"Invalid folder ID: {folder_id}")
            
            updated_file = await self.files_collection.find_one_and_update(
                {"_id": ObjectId(file_id), "userId": user_id},
                {"$set": update_data},
                return_document=True
            )
            
            return serialize_document(updated_file) if updated_file else None
        except Exception as e:
            raise Exception(f"Failed to update file: {str(e)}")
    
    async def delete_file(self, file_id: str, user_id: str) -> bool:
        """Delete a file"""
        try:
            file_doc = await self.files_collection.find_one({
                "_id": ObjectId(file_id),
                "userId": user_id
            })
            
            if not file_doc:
                raise Exception("File not found")
            
            # Delete from GridFS
            await self.gridfs_service.delete_file(str(file_doc["gridFsFileId"]))
            
            # Delete metadata
            result = await self.files_collection.delete_one({
                "_id": ObjectId(file_id),
                "userId": user_id
            })
            
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def search_files(self, user_id: str, query: str) -> List[dict]:
        """Search files by name"""
        files = await self.files_collection.find({
            "userId": user_id,
            "name": {"$regex": query, "$options": "i"}
        }).to_list(None)
        
        return serialize_documents(files)
