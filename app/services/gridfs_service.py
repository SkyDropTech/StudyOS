# app/services/gridfs_service.py
"""GridFS service for handling file storage and retrieval"""

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId
from typing import Optional
import io


class GridFSService:
    """Service for managing GridFS operations"""
    
    def __init__(self, grid_fs: AsyncIOMotorGridFSBucket):
        self.grid_fs = grid_fs
    
    async def upload_file(
        self,
        filename: str,
        content: str,
        user_id: str,
        folder_id: Optional[str] = None
    ) -> str:
        """
        Upload file content to GridFS
        Returns the GridFS file ID
        """
        file_bytes = content.encode('utf-8')
        
        metadata = {
            "userId": user_id,
            "folderId": folder_id,
            "originalFilename": filename
        }
        
        grid_fs_id = await self.grid_fs.upload_from_stream(
            filename,
            io.BytesIO(file_bytes),
            metadata=metadata
        )
        
        return str(grid_fs_id)
    
    async def download_file(self, grid_fs_id: str) -> str:
        """
        Download file content from GridFS
        Returns the file content as string
        """
        try:
            grid_fs_file_id = ObjectId(grid_fs_id)
            grid_out = await self.grid_fs.open_download_stream(grid_fs_file_id)
            content = await grid_out.read()
            await grid_out.close()
            return content.decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to download file: {str(e)}")
    
    async def delete_file(self, grid_fs_id: str) -> bool:
        """Delete file from GridFS"""
        try:
            grid_fs_file_id = ObjectId(grid_fs_id)
            await self.grid_fs.delete(grid_fs_file_id)
            return True
        except Exception as e:
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def update_file(
        self,
        grid_fs_id: str,
        new_content: str
    ) -> str:
        """
        Update file in GridFS by deleting old and uploading new
        Returns the new GridFS file ID
        """
        try:
            # Get metadata from old file
            old_grid_fs_id = ObjectId(grid_fs_id)
            grid_out = await self.grid_fs.open_download_stream(old_grid_fs_id)
            old_metadata = grid_out.metadata or {}
            await grid_out.close()
            
            # Delete old file
            await self.delete_file(grid_fs_id)
            
            # Upload new file with same metadata
            new_file_bytes = new_content.encode('utf-8')
            
            new_grid_fs_id = await self.grid_fs.upload_from_stream(
                old_metadata.get('originalFilename', 'notebook.html'),
                io.BytesIO(new_file_bytes),
                metadata=old_metadata
            )
            
            return str(new_grid_fs_id)
        except Exception as e:
            raise Exception(f"Failed to update file: {str(e)}")
