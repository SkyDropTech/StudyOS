# app/services/smartnotebook_service.py
"""Smart Notebook service — manages notebooks (binders), the folders inside them,
and the items (notes / links / uploaded files of any kind) inside those folders.

Everything is persisted in MongoDB:
- notebooks_collection: one doc per notebook (title, icon, color)
- nb_folders_collection: folders that belong to a notebook (nested via parentId)
- nb_items_collection: notes / links / files that belong to a notebook + optional folder.
  Binary file content (PDF, PPTX, images, etc.) lives in GridFS; the item doc just
  references the GridFS id + records the original mime type / size / filename.
"""

from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime
from typing import Optional, List
from app.utils.serializer import serialize_document, serialize_documents


class SmartNotebookService:
    def __init__(
        self,
        notebooks_collection: AsyncIOMotorCollection,
        nb_folders_collection: AsyncIOMotorCollection,
        nb_items_collection: AsyncIOMotorCollection,
        gridfs_service,  # GridFSService (text) reused for its bucket access pattern
    ):
        self.notebooks_collection = notebooks_collection
        self.nb_folders_collection = nb_folders_collection
        self.nb_items_collection = nb_items_collection
        self.gridfs_service = gridfs_service

        # Binary-safe GridFS wrapper, sharing the same underlying bucket
        from app.services.binary_gridfs_service import BinaryGridFSService
        self.binary_gridfs = BinaryGridFSService(gridfs_service.grid_fs)

    # ==================== NOTEBOOK (BINDER) ====================

    async def create_notebook(
        self, user_id: str, title: str, icon: str, color: str, description: Optional[str] = None
    ) -> dict:
        now = datetime.utcnow()
        doc = {
            "userId": user_id,
            "title": title,
            "icon": icon or "fa-solid fa-book",
            "color": color or "#6D5EF7",
            "description": description,
            "createdAt": now,
            "updatedAt": now,
        }
        result = await self.notebooks_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_document(doc)

    async def get_user_notebooks(self, user_id: str) -> List[dict]:
        cursor = self.notebooks_collection.find({"userId": user_id}).sort("createdAt", -1)
        notebooks = await cursor.to_list(None)
        notebooks = serialize_documents(notebooks)

        # Attach quick counts (folders + items) for the dashboard / hub cards
        for nb in notebooks:
            nb_id = nb["_id"]
            folder_count = await self.nb_folders_collection.count_documents(
                {"userId": user_id, "notebookId": ObjectId(nb_id)}
            )
            item_count = await self.nb_items_collection.count_documents(
                {"userId": user_id, "notebookId": ObjectId(nb_id)}
            )
            nb["folderCount"] = folder_count
            nb["itemCount"] = item_count

        return notebooks

    async def get_notebook(self, notebook_id: str, user_id: str) -> Optional[dict]:
        try:
            doc = await self.notebooks_collection.find_one(
                {"_id": ObjectId(notebook_id), "userId": user_id}
            )
            return serialize_document(doc) if doc else None
        except Exception as e:
            raise Exception(f"Invalid notebook ID: {str(e)}")

    async def update_notebook(
        self,
        notebook_id: str,
        user_id: str,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        color: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[dict]:
        update_data = {"updatedAt": datetime.utcnow()}
        if title is not None:
            update_data["title"] = title
        if icon is not None:
            update_data["icon"] = icon
        if color is not None:
            update_data["color"] = color
        if description is not None:
            update_data["description"] = description

        updated = await self.notebooks_collection.find_one_and_update(
            {"_id": ObjectId(notebook_id), "userId": user_id},
            {"$set": update_data},
            return_document=True,
        )
        return serialize_document(updated) if updated else None

    async def delete_notebook(self, notebook_id: str, user_id: str) -> bool:
        """Delete a notebook and everything inside it (folders + items + GridFS blobs)"""
        try:
            nb_oid = ObjectId(notebook_id)

            # Delete all items (and their GridFS blobs) in this notebook
            items = await self.nb_items_collection.find(
                {"userId": user_id, "notebookId": nb_oid}
            ).to_list(None)
            for item in items:
                if item.get("itemType") == "file" and item.get("gridFsFileId"):
                    await self.binary_gridfs.delete_bytes(str(item["gridFsFileId"]))
            await self.nb_items_collection.delete_many({"userId": user_id, "notebookId": nb_oid})

            # Delete all folders in this notebook
            await self.nb_folders_collection.delete_many({"userId": user_id, "notebookId": nb_oid})

            # Delete the notebook itself
            result = await self.notebooks_collection.delete_one(
                {"_id": nb_oid, "userId": user_id}
            )
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Failed to delete notebook: {str(e)}")

    # ==================== FOLDERS ====================

    async def create_folder(
        self, notebook_id: str, user_id: str, name: str, parent_id: Optional[str] = None
    ) -> dict:
        now = datetime.utcnow()
        doc = {
            "userId": user_id,
            "notebookId": ObjectId(notebook_id),
            "name": name,
            "parentId": ObjectId(parent_id) if parent_id else None,
            "createdAt": now,
            "updatedAt": now,
        }
        result = await self.nb_folders_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_document(doc)

    async def get_folders(self, notebook_id: str, user_id: str) -> List[dict]:
        cursor = self.nb_folders_collection.find(
            {"userId": user_id, "notebookId": ObjectId(notebook_id)}
        )
        folders = await cursor.to_list(None)
        return serialize_documents(folders)

    async def update_folder(
        self,
        folder_id: str,
        user_id: str,
        name: Optional[str] = None,
        parent_id: Optional[str] = None,
    ) -> Optional[dict]:
        update_data = {"updatedAt": datetime.utcnow()}
        if name:
            update_data["name"] = name
        if parent_id is not None:
            update_data["parentId"] = None if parent_id == "" else ObjectId(parent_id)

        updated = await self.nb_folders_collection.find_one_and_update(
            {"_id": ObjectId(folder_id), "userId": user_id},
            {"$set": update_data},
            return_document=True,
        )
        return serialize_document(updated) if updated else None

    async def delete_folder(self, folder_id: str, user_id: str) -> bool:
        """Delete a folder, its sub-folders, and all items within (recursive)"""
        try:
            folder_oid = ObjectId(folder_id)

            # Find sub-folders recursively
            to_delete = [folder_oid]
            frontier = [folder_oid]
            while frontier:
                children = await self.nb_folders_collection.find(
                    {"userId": user_id, "parentId": {"$in": frontier}}
                ).to_list(None)
                child_ids = [c["_id"] for c in children]
                to_delete.extend(child_ids)
                frontier = child_ids

            # Delete items inside any of these folders
            items = await self.nb_items_collection.find(
                {"userId": user_id, "folderId": {"$in": to_delete}}
            ).to_list(None)
            for item in items:
                if item.get("itemType") == "file" and item.get("gridFsFileId"):
                    await self.binary_gridfs.delete_bytes(str(item["gridFsFileId"]))
            await self.nb_items_collection.delete_many(
                {"userId": user_id, "folderId": {"$in": to_delete}}
            )

            # Delete the folders themselves
            result = await self.nb_folders_collection.delete_many(
                {"userId": user_id, "_id": {"$in": to_delete}}
            )
            return result.deleted_count > 0
        except Exception as e:
            raise Exception(f"Failed to delete folder: {str(e)}")

    # ==================== ITEMS (notes / links / files) ====================

    async def create_note(
        self, notebook_id: str, user_id: str, name: str, content: str, folder_id: Optional[str] = None
    ) -> dict:
        now = datetime.utcnow()
        doc = {
            "userId": user_id,
            "notebookId": ObjectId(notebook_id),
            "folderId": ObjectId(folder_id) if folder_id else None,
            "itemType": "note",
            "name": name,
            "content": content,
            "createdAt": now,
            "updatedAt": now,
        }
        result = await self.nb_items_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_document(doc)

    async def create_link(
        self,
        notebook_id: str,
        user_id: str,
        name: str,
        url: str,
        link_kind: str = "video",
        folder_id: Optional[str] = None,
    ) -> dict:
        now = datetime.utcnow()
        doc = {
            "userId": user_id,
            "notebookId": ObjectId(notebook_id),
            "folderId": ObjectId(folder_id) if folder_id else None,
            "itemType": "link",
            "name": name,
            "url": url,
            "linkKind": link_kind,
            "createdAt": now,
            "updatedAt": now,
        }
        result = await self.nb_items_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_document(doc)

    async def create_file(
        self,
        notebook_id: str,
        user_id: str,
        filename: str,
        data: bytes,
        content_type: str,
        folder_id: Optional[str] = None,
    ) -> dict:
        now = datetime.utcnow()

        grid_fs_id = await self.binary_gridfs.upload_bytes(
            filename, data, content_type, user_id,
            extra_metadata={"notebookId": notebook_id, "folderId": folder_id},
        )

        doc = {
            "userId": user_id,
            "notebookId": ObjectId(notebook_id),
            "folderId": ObjectId(folder_id) if folder_id else None,
            "itemType": "file",
            "name": filename,
            "mimeType": content_type,
            "size": len(data),
            "gridFsFileId": ObjectId(grid_fs_id),
            "createdAt": now,
            "updatedAt": now,
        }
        result = await self.nb_items_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return serialize_document(doc)

    async def get_items(self, notebook_id: str, user_id: str) -> List[dict]:
        """Get ALL items in a notebook (across all folders) — frontend builds the tree client-side"""
        cursor = self.nb_items_collection.find(
            {"userId": user_id, "notebookId": ObjectId(notebook_id)}
        )
        items = await cursor.to_list(None)
        return serialize_documents(items)

    async def get_item(self, item_id: str, user_id: str) -> Optional[dict]:
        try:
            doc = await self.nb_items_collection.find_one(
                {"_id": ObjectId(item_id), "userId": user_id}
            )
            return serialize_document(doc) if doc else None
        except Exception as e:
            raise Exception(f"Invalid item ID: {str(e)}")

    async def get_file_bytes(self, item_id: str, user_id: str):
        """Returns (bytes, filename, content_type) for a file item"""
        doc = await self.nb_items_collection.find_one(
            {"_id": ObjectId(item_id), "userId": user_id, "itemType": "file"}
        )
        if not doc:
            raise Exception("File not found")
        data = await self.binary_gridfs.download_bytes(str(doc["gridFsFileId"]))
        return data, doc.get("name", "file"), doc.get("mimeType", "application/octet-stream")

    async def update_item(
        self,
        item_id: str,
        user_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        url: Optional[str] = None,
        folder_id: Optional[str] = None,
    ) -> Optional[dict]:
        update_data = {"updatedAt": datetime.utcnow()}
        if name is not None:
            update_data["name"] = name
        if content is not None:
            update_data["content"] = content
        if url is not None:
            update_data["url"] = url
        if folder_id is not None:
            update_data["folderId"] = None if folder_id == "" else ObjectId(folder_id)

        updated = await self.nb_items_collection.find_one_and_update(
            {"_id": ObjectId(item_id), "userId": user_id},
            {"$set": update_data},
            return_document=True,
        )
        return serialize_document(updated) if updated else None

    async def delete_item(self, item_id: str, user_id: str) -> bool:
        doc = await self.nb_items_collection.find_one(
            {"_id": ObjectId(item_id), "userId": user_id}
        )
        if not doc:
            return False

        if doc.get("itemType") == "file" and doc.get("gridFsFileId"):
            await self.binary_gridfs.delete_bytes(str(doc["gridFsFileId"]))

        result = await self.nb_items_collection.delete_one(
            {"_id": ObjectId(item_id), "userId": user_id}
        )
        return result.deleted_count > 0

    async def search(self, notebook_id: str, user_id: str, query: str) -> List[dict]:
        cursor = self.nb_items_collection.find({
            "userId": user_id,
            "notebookId": ObjectId(notebook_id),
            "name": {"$regex": query, "$options": "i"},
        })
        items = await cursor.to_list(None)
        return serialize_documents(items)
