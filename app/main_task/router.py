from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.main_task.model import MainTask
from app.main_task.schema import MainTaskCreate, MainTaskRead, MainTaskUpdate, MainTaskWithSubTasks

router = APIRouter(prefix="/main-tasks", tags=["Main Tasks"])


def serialize_main_task(task: MainTask, include_sub_tasks: bool = False) -> dict:
    data = {
        "id": task.id,
        "title": task.title,
        "slug": task.slug,
        "description": task.description,
        "about": task.description,
        "due_date": None,
        "created_date": task.created_at.isoformat() if task.created_at else None,
        "updated_date": task.updated_at.isoformat() if task.updated_at else None,
        "assign_to": task.assign_to,
    }
    if include_sub_tasks:
        data["sub_tasks"] = [
            {
                "id": sub_task.id,
                "main_task_id": sub_task.main_task_id,
                "title": sub_task.title,
                "slug": sub_task.slug,
                "description": sub_task.description,
                "about": sub_task.description,
                "due_date": None,
                "created_date": sub_task.created_at.isoformat() if sub_task.created_at else None,
                "updated_date": sub_task.updated_at.isoformat() if sub_task.updated_at else None,
                "assign_to": sub_task.assign_to,
            }
            for sub_task in task.sub_tasks
        ]
    return data


def ensure_main_task_slug_is_unique(db: Session, slug: str, current_task_id: int | None = None) -> None:
    existing_task = db.query(MainTask).filter(MainTask.slug == slug).first()
    if existing_task and existing_task.id != current_task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")


@router.get("/", response_model=list[MainTaskRead])
def list_main_tasks(db: Session = Depends(get_db)):
    tasks = db.query(MainTask).order_by(MainTask.id).all()
    return [serialize_main_task(task) for task in tasks]


@router.get("/{task_id}", response_model=MainTaskWithSubTasks)
def get_main_task(task_id: int, db: Session = Depends(get_db)):
    task = (
        db.query(MainTask)
        .options(selectinload(MainTask.sub_tasks))
        .filter(MainTask.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main task not found")
    return serialize_main_task(task, include_sub_tasks=True)


@router.post("/", response_model=MainTaskRead, status_code=status.HTTP_201_CREATED)
def create_main_task(payload: MainTaskCreate, db: Session = Depends(get_db)):
    ensure_main_task_slug_is_unique(db, payload.slug)

    task = MainTask(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        assign_to=payload.assign_to,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return serialize_main_task(task)


@router.put("/{task_id}", response_model=MainTaskRead)
def replace_main_task(task_id: int, payload: MainTaskCreate, db: Session = Depends(get_db)):
    task = db.query(MainTask).filter(MainTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main task not found")

    ensure_main_task_slug_is_unique(db, payload.slug, current_task_id=task.id)

    task.title = payload.title
    task.slug = payload.slug
    task.description = payload.description
    task.assign_to = payload.assign_to

    db.commit()
    db.refresh(task)
    return serialize_main_task(task)


@router.patch("/{task_id}", response_model=MainTaskRead)
def update_main_task(task_id: int, payload: MainTaskUpdate, db: Session = Depends(get_db)):
    task = db.query(MainTask).filter(MainTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main task not found")

    updates = payload.model_dump(exclude_unset=True)

    if "slug" in updates:
        ensure_main_task_slug_is_unique(db, updates["slug"], current_task_id=task.id)

    if "title" in updates:
        task.title = updates["title"]
    if "slug" in updates:
        task.slug = updates["slug"]
    if "description" in updates:
        task.description = updates["description"]
    if "assign_to" in updates:
        task.assign_to = updates["assign_to"]

    db.commit()
    db.refresh(task)
    return serialize_main_task(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_main_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(MainTask).filter(MainTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main task not found")

    db.delete(task)
    db.commit()
