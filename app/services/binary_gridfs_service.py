# app/services/binary_gridfs_service.py
"""GridFS service variant that handles raw binary content (PDFs, PPTX, images, etc.)
Used by Smart Notebooks, where users can store any file type — not just text/code."""

from motor.motor_asyncio import AsyncIOMotorGridFSBucket
from bson import ObjectId
from typing import Optional
import io


class BinaryGridFSService:
    """Service for storing arbitrary binary files in GridFS"""

    def __init__(self, grid_fs: AsyncIOMotorGridFSBucket):
        self.grid_fs = grid_fs

    async def upload_bytes(
        self,
        filename: str,
        data: bytes,
        content_type: str,
        user_id: str,
        extra_metadata: Optional[dict] = None,
    ) -> str:
        """Upload raw bytes to GridFS. Returns the GridFS file ID as a string."""
        metadata = {
            "userId": user_id,
            "contentType": content_type,
            "originalFilename": filename,
        }
        if extra_metadata:
            metadata.update(extra_metadata)

        grid_fs_id = await self.grid_fs.upload_from_stream(
            filename,
            io.BytesIO(data),
            metadata=metadata,
        )
        return str(grid_fs_id)

    async def download_bytes(self, grid_fs_id: str) -> bytes:
        """Download raw bytes from GridFS"""
        grid_fs_file_id = ObjectId(grid_fs_id)
        grid_out = await self.grid_fs.open_download_stream(grid_fs_file_id)
        data = await grid_out.read()
        await grid_out.close()
        return data

    async def get_metadata(self, grid_fs_id: str) -> dict:
        """Fetch only metadata/info for a stored file (filename, contentType, length)"""
        grid_fs_file_id = ObjectId(grid_fs_id)
        grid_out = await self.grid_fs.open_download_stream(grid_fs_file_id)
        info = {
            "filename": grid_out.filename,
            "length": grid_out.length,
            "metadata": grid_out.metadata or {},
        }
        await grid_out.close()
        return info

    async def delete_bytes(self, grid_fs_id: str) -> bool:
        """Delete a file from GridFS"""
        try:
            await self.grid_fs.delete(ObjectId(grid_fs_id))
            return True
        except Exception:
            return False
