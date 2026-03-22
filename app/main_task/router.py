from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.main_task.model import MainTask
from app.main_task.schema import MainTaskCreate, MainTaskRead, MainTaskUpdate, MainTaskWithSubTasks

router = APIRouter(prefix="/main-tasks", tags=["Main Tasks"])


def ensure_main_task_slug_is_unique(db: Session, slug: str, current_task_id: int | None = None) -> None:
    existing_task = db.query(MainTask).filter(MainTask.slug == slug).first()
    if existing_task and existing_task.id != current_task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")


@router.get("/", response_model=list[MainTaskRead])
def list_main_tasks(
    status_filter: str | None = Query(default=None, alias="status"),
    assign_to: str | None = Query(default=None),
    slug: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(MainTask).order_by(MainTask.id)

    if status_filter:
        query = query.filter(MainTask.status == status_filter)
    if assign_to:
        query = query.filter(MainTask.assign_to == assign_to)
    if slug:
        query = query.filter(MainTask.slug == slug)

    return query.offset(skip).limit(limit).all()


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
    return task


@router.post("/", response_model=MainTaskRead, status_code=status.HTTP_201_CREATED)
def create_main_task(payload: MainTaskCreate, db: Session = Depends(get_db)):
    ensure_main_task_slug_is_unique(db, payload.slug)

    task = MainTask(
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        status=payload.status,
        assign_to=payload.assign_to,
        due_date=payload.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.put("/{task_id}", response_model=MainTaskRead)
def replace_main_task(task_id: int, payload: MainTaskCreate, db: Session = Depends(get_db)):
    task = db.query(MainTask).filter(MainTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main task not found")

    ensure_main_task_slug_is_unique(db, payload.slug, current_task_id=task.id)

    task.title = payload.title
    task.slug = payload.slug
    task.description = payload.description
    task.status = payload.status
    task.assign_to = payload.assign_to
    task.due_date = payload.due_date

    db.commit()
    db.refresh(task)
    return task


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
    if "status" in updates:
        task.status = updates["status"]
    if "assign_to" in updates:
        task.assign_to = updates["assign_to"]
    if "due_date" in updates:
        task.due_date = updates["due_date"]

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_main_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(MainTask).filter(MainTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main task not found")

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
