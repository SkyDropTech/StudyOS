# app/routes/tasks.py
"""Routes for the daily To-Do list"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models.tasks import TaskCreate, TaskUpdate

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

DEFAULT_USER_ID = "Skydrop"  # single-user app; swap for real auth user_id later


def _service():
    from app.database import get_tasks_service
    return get_tasks_service()


@router.get("")
async def list_tasks(
    user_id: str = Query(default=DEFAULT_USER_ID),
    completed: Optional[bool] = Query(default=None),
):
    """List all tasks for a user (optionally filtered by completion status)"""
    try:
        tasks = await _service().get_user_tasks(user_id, completed=completed)
        return {"status": "success", "data": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def task_stats(user_id: str = Query(default=DEFAULT_USER_ID)):
    """Quick counts for the dashboard widget"""
    try:
        stats = await _service().get_stats(user_id)
        return {"status": "success", "data": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_task(payload: TaskCreate, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Create a new task"""
    try:
        if not payload.title or not payload.title.strip():
            raise HTTPException(status_code=400, detail="Title is required")
        task = await _service().create_task(
            user_id,
            payload.title.strip(),
            payload.notes,
            payload.priority,
            payload.due_date,
            payload.tag,
        )
        return {"status": "success", "data": task}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{task_id}")
async def get_task(task_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Get a single task"""
    try:
        task = await _service().get_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "data": task}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{task_id}")
async def update_task(task_id: str, payload: TaskUpdate, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Update a task"""
    try:
        task = await _service().update_task(
            task_id,
            user_id,
            payload.title,
            payload.notes,
            payload.priority,
            payload.due_date,
            payload.tag,
            payload.completed,
        )
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "data": task}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{task_id}/toggle")
async def toggle_task(task_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Toggle a task's completed status"""
    try:
        task = await _service().toggle_task(task_id, user_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "data": task}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(task_id: str, user_id: str = Query(default=DEFAULT_USER_ID)):
    """Delete a task"""
    try:
        deleted = await _service().delete_task(task_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"status": "success", "message": "Task deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
