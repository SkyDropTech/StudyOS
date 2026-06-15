# app/example_usage.py
"""
Example usage of the StudyOS Notebook API
Shows how to interact with the MongoDB-backed notebook system
"""

import asyncio
from app.database import get_notebook_service
from app.services.gridfs_service import GridFSService
from app.database import grid_fs


async def example_workflow():
    """
    Demonstrates the complete workflow:
    1. Create a folder for a user
    2. Create notebook files in that folder
    3. Read and update files
    4. Search for files
    """
    
    # Initialize services
    notebook_service = get_notebook_service()
    
    # User ID - this would come from authentication
    user_id = "Skydrop"
    
    print("=" * 60)
    print("StudyOS Notebook Example Workflow")
    print("=" * 60)
    print()
    
    try:
        # ===== 1. CREATE FOLDERS =====
        print("📁 Creating folders for user:", user_id)
        print("-" * 60)
        
        projects_folder = await notebook_service.create_folder(
            user_id=user_id,
            name="Projects"
        )
        print(f"✅ Created folder: {projects_folder['name']}")
        print(f"   ID: {projects_folder['_id']}")
        
        work_folder = await notebook_service.create_folder(
            user_id=user_id,
            name="Work"
        )
        print(f"✅ Created folder: {work_folder['name']}")
        print()
        
        # ===== 2. CREATE NOTEBOOK FILES =====
        print("📝 Creating notebook files")
        print("-" * 60)
        
        # Sample notebook HTML content
        notebook_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>My Notebook</title>
        </head>
        <body>
            <h1>Study Notes</h1>
            <p>These are my notes from today's lecture.</p>
            <ul>
                <li>Point 1: Machine Learning basics</li>
                <li>Point 2: Neural Networks</li>
                <li>Point 3: Deep Learning</li>
            </ul>
        </body>
        </html>
        """
        
        file1 = await notebook_service.create_file(
            user_id=user_id,
            name="ML_Basics.html",
            content=notebook_html,
            folder_id=projects_folder['_id']
        )
        print(f"✅ Created file: {file1['name']}")
        print(f"   ID: {file1['_id']}")
        print(f"   Size: {file1['size']} bytes")
        print(f"   Stored in folder: Projects")
        
        file2 = await notebook_service.create_file(
            user_id=user_id,
            name="Work_Notes.html",
            content=notebook_html,
            folder_id=work_folder['_id']
        )
        print(f"✅ Created file: {file2['name']}")
        print()
        
        # ===== 3. LIST USER'S DATA =====
        print("📊 Listing all user data")
        print("-" * 60)
        
        all_folders = await notebook_service.get_user_folders(user_id)
        print(f"Folders: {len(all_folders)}")
        for folder in all_folders:
            print(f"  • {folder['name']} (ID: {folder['_id']})")
        
        all_files = await notebook_service.get_user_files(user_id)
        print(f"\nFiles: {len(all_files)}")
        for file in all_files:
            folder_name = next(
                (f['name'] for f in all_folders if f['_id'] == file.get('folder_id')),
                "Root"
            )
            print(f"  • {file['name']} (Folder: {folder_name})")
        print()
        
        # ===== 4. READ FILE CONTENT =====
        print("📖 Reading file content")
        print("-" * 60)
        
        content = await notebook_service.get_file_content(
            file_id=file1['_id'],
            user_id=user_id
        )
        print(f"File: {file1['name']}")
        print(f"Content length: {len(content)} characters")
        print(f"Content preview: {content[:100]}...")
        print()
        
        # ===== 5. UPDATE FILE =====
        print("✏️  Updating file")
        print("-" * 60)
        
        updated_content = notebook_html.replace("Study Notes", "Updated Study Notes")
        updated_file = await notebook_service.update_file(
            file_id=file1['_id'],
            user_id=user_id,
            content=updated_content
        )
        print(f"✅ Updated file: {updated_file['name']}")
        print(f"   New size: {updated_file['size']} bytes")
        print()
        
        # ===== 6. SEARCH FILES =====
        print("🔍 Searching files")
        print("-" * 60)
        
        search_results = await notebook_service.search_files(
            user_id=user_id,
            query="ML"
        )
        print(f"Search for 'ML': found {len(search_results)} files")
        for result in search_results:
            print(f"  • {result['name']}")
        print()
        
        # ===== 7. GET FILES IN FOLDER =====
        print("📂 Files in 'Projects' folder")
        print("-" * 60)
        
        folder_files = await notebook_service.get_user_files(
            user_id=user_id,
            folder_id=projects_folder['_id']
        )
        print(f"Found: {len(folder_files)} files")
        for file in folder_files:
            print(f"  • {file['name']}")
        print()
        
        # ===== 8. DELETE FILE =====
        print("🗑️  Deleting file")
        print("-" * 60)
        
        success = await notebook_service.delete_file(
            file_id=file2['_id'],
            user_id=user_id
        )
        print(f"✅ Deleted: {file2['name']}")
        print()
        
        print("=" * 60)
        print("✅ Example workflow completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(example_workflow())
