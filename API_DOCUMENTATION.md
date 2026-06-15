# API_DOCUMENTATION.md
# StudyOS API Documentation

## Overview
StudyOS is a MongoDB-backed notebook system with the following features:
- User-isolated folder and file organization
- HTML notebook storage in GridFS
- Full CRUD operations
- Search functionality
- Proper data serialization

## Database Architecture

### Collections
1. **folders**: Stores folder metadata
   - `_id`: ObjectId
   - `userId`: User identifier (e.g., "Skydrop")
   - `name`: Folder name
   - `parentId`: Parent folder reference (null for root)
   - `path`: Folder path
   - `createdAt`: Creation timestamp
   - `updatedAt`: Last update timestamp

2. **files**: Stores file/notebook metadata
   - `_id`: ObjectId
   - `userId`: User identifier
   - `name`: File name
   - `folderId`: Parent folder reference
   - `size`: File size in bytes
   - `mimeType`: MIME type (usually "text/html")
   - `gridFsFileId`: Reference to GridFS file
   - `createdAt`: Creation timestamp
   - `updatedAt`: Last update timestamp

3. **fs.files** & **fs.chunks**: GridFS collections for binary storage
   - Automatically managed by Motor's GridFSBucket
   - Stores actual file content

## API Endpoints

### Authentication Routes
Base: `/api/auth`

#### Get Current User
```
GET /api/auth/current-user
Response:
{
  "user_id": "Skydrop",
  "username": "Skydrop",
  "email": "user@example.com"
}
```

#### Login
```
POST /api/auth/login
Body: {
  "username": "Skydrop",
  "password": "password123"
}
Response:
{
  "status": "success",
  "user_id": "Skydrop",
  "token": "token_value"
}
```

### Notebook Routes
Base: `/api/notebook`

#### Folders

##### Create Folder
```
POST /api/notebook/folders
Query Parameters:
  - user_id: "Skydrop" (required)
  - name: "Projects" (required)
  - parent_id: null or folder_id (optional)

Response:
{
  "_id": "507f1f77bcf86cd799439011",
  "userId": "Skydrop",
  "name": "Projects",
  "parentId": null,
  "path": "/",
  "createdAt": "2024-01-15T10:30:00",
  "updatedAt": "2024-01-15T10:30:00"
}
```

##### Get User Folders
```
GET /api/notebook/folders?user_id=Skydrop
Response: [
  {
    "_id": "507f1f77bcf86cd799439011",
    "userId": "Skydrop",
    "name": "Projects",
    ...
  }
]
```

##### Get Specific Folder
```
GET /api/notebook/folders/{folder_id}?user_id=Skydrop
Response: {...folder object...}
```

##### Update Folder
```
PUT /api/notebook/folders/{folder_id}
Query: user_id=Skydrop
Body: {
  "name": "New Folder Name"
}
Response: {...updated folder...}
```

##### Delete Folder
```
DELETE /api/notebook/folders/{folder_id}?user_id=Skydrop
Response: {
  "status": "success",
  "message": "Folder deleted"
}
```

#### Files/Notebooks

##### Create File
```
POST /api/notebook/files?user_id=Skydrop
Body: {
  "name": "ML_Basics.html",
  "content": "<html>...</html>",
  "folder_id": null or folder_id
}
Response:
{
  "_id": "507f1f77bcf86cd799439012",
  "userId": "Skydrop",
  "name": "ML_Basics.html",
  "folderId": null,
  "size": 1024,
  "mimeType": "text/html",
  "gridFsFileId": "607f1f77bcf86cd799439013",
  "createdAt": "2024-01-15T10:30:00",
  "updatedAt": "2024-01-15T10:30:00"
}
```

##### Get User Files
```
GET /api/notebook/files?user_id=Skydrop&folder_id={optional}
Response: [{...file objects...}]
```

##### Get Specific File Metadata
```
GET /api/notebook/files/{file_id}?user_id=Skydrop
Response: {...file object...}
```

##### Get File Content
```
GET /api/notebook/files/{file_id}/content?user_id=Skydrop
Response: {
  "content": "<html>...</html>"
}
```

##### Update File
```
PUT /api/notebook/files/{file_id}?user_id=Skydrop
Body: {
  "name": "New Name.html",
  "content": "<html>...</html>"
}
Response: {...updated file...}
```

##### Delete File
```
DELETE /api/notebook/files/{file_id}?user_id=Skydrop
Response: {
  "status": "success",
  "message": "File deleted"
}
```

##### Search Files
```
GET /api/notebook/search?user_id=Skydrop&query=ML
Response: [{...matching files...}]
```

### Files Routes
Base: `/api/files`

#### Upload File
```
POST /api/files/upload
Body: FormData with file
Query: user_id=Skydrop
```

#### Get File Info
```
GET /api/files/info/{file_id}?user_id=Skydrop
```

## Project Structure

```
app/
├── main.py                 # FastAPI app & frontend routes
├── database.py             # MongoDB configuration
├── routes/
│   ├── __init__.py
│   ├── notebook.py         # Notebook API endpoints
│   ├── auth.py            # Auth endpoints
│   └── files.py           # File upload endpoints
├── services/
│   ├── __init__.py
│   ├── gridfs_service.py  # GridFS operations
│   └── notebook_service.py # Business logic
├── models/
│   ├── __init__.py
│   └── notebook.py        # Pydantic models
└── utils/
    ├── __init__.py
    ├── serializer.py      # JSON serialization
    └── objectid.py        # ObjectId helpers
```

## Usage Examples

### Create a Notebook for User "Skydrop"
```bash
curl -X POST "http://localhost:8000/api/notebook/files?user_id=Skydrop" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Notes.html",
    "content": "<h1>Study Notes</h1>",
    "folder_id": null
  }'
```

### Get All Notebooks for User
```bash
curl "http://localhost:8000/api/notebook/files?user_id=Skydrop"
```

### Update Notebook Content
```bash
curl -X PUT "http://localhost:8000/api/notebook/files/{file_id}?user_id=Skydrop" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "<h1>Updated Notes</h1>"
  }'
```

### Delete Notebook
```bash
curl -X DELETE "http://localhost:8000/api/notebook/files/{file_id}?user_id=Skydrop"
```

## Data Storage Flow

1. **Upload**: HTML content → GridFS (binary) + metadata → files collection
2. **Read**: Request file_id → fetch metadata from files → read binary from GridFS
3. **Update**: New content → new GridFS file → delete old file → update metadata
4. **Delete**: Remove file from files collection → delete from GridFS

## Indexes

Automatically created for performance:
- `folders.userId`
- `files.userId`
- `files.name` (for search)

## Authentication

Currently uses a simple user_id query parameter. 
TODO: Implement proper JWT authentication

## Error Handling

All endpoints return proper HTTP status codes:
- 200: Success
- 400: Bad request
- 404: Not found
- 500: Server error

Error response format:
```json
{
  "error": "Description of error",
  "status_code": 400,
  "timestamp": "2024-01-15T10:30:00"
}
```
