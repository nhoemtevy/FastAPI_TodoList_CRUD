from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.main_task.model import MainTask
from app.sub_task.model import SubTask
from app.sub_task.schema import SubTaskCreate, SubTaskRead, SubTaskUpdate

router = APIRouter(prefix="/sub-tasks", tags=["Sub Tasks"])


def ensure_main_task_exists(db: Session, main_task_id: int) -> None:
    main_task = db.query(MainTask).filter(MainTask.id == main_task_id).first()
    if not main_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Main task not found")


def ensure_sub_task_slug_is_unique(
    db: Session, slug: str, current_sub_task_id: int | None = None
) -> None:
    existing_sub_task = db.query(SubTask).filter(SubTask.slug == slug).first()
    if existing_sub_task and existing_sub_task.id != current_sub_task_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already exists")


@router.get("/", response_model=list[SubTaskRead])
def list_sub_tasks(
    main_task_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    assign_to: str | None = Query(default=None),
    slug: str | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(SubTask).order_by(SubTask.id)

    if main_task_id is not None:
        query = query.filter(SubTask.main_task_id == main_task_id)
    if status_filter:
        query = query.filter(SubTask.status == status_filter)
    if assign_to:
        query = query.filter(SubTask.assign_to == assign_to)
    if slug:
        query = query.filter(SubTask.slug == slug)

    return query.offset(skip).limit(limit).all()


@router.get("/{sub_task_id}", response_model=SubTaskRead)
def get_sub_task(sub_task_id: int, db: Session = Depends(get_db)):
    sub_task = db.query(SubTask).filter(SubTask.id == sub_task_id).first()
    if not sub_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub task not found")
    return sub_task


@router.post("/", response_model=SubTaskRead, status_code=status.HTTP_201_CREATED)
def create_sub_task(payload: SubTaskCreate, db: Session = Depends(get_db)):
    ensure_main_task_exists(db, payload.main_task_id)
    ensure_sub_task_slug_is_unique(db, payload.slug)

    sub_task = SubTask(
        main_task_id=payload.main_task_id,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        status=payload.status,
        assign_to=payload.assign_to,
        due_date=payload.due_date,
    )
    db.add(sub_task)
    db.commit()
    db.refresh(sub_task)
    return sub_task


@router.put("/{sub_task_id}", response_model=SubTaskRead)
def replace_sub_task(sub_task_id: int, payload: SubTaskCreate, db: Session = Depends(get_db)):
    sub_task = db.query(SubTask).filter(SubTask.id == sub_task_id).first()
    if not sub_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub task not found")

    ensure_main_task_exists(db, payload.main_task_id)
    ensure_sub_task_slug_is_unique(db, payload.slug, current_sub_task_id=sub_task.id)

    sub_task.main_task_id = payload.main_task_id
    sub_task.title = payload.title
    sub_task.slug = payload.slug
    sub_task.description = payload.description
    sub_task.status = payload.status
    sub_task.assign_to = payload.assign_to
    sub_task.due_date = payload.due_date

    db.commit()
    db.refresh(sub_task)
    return sub_task


@router.patch("/{sub_task_id}", response_model=SubTaskRead)
def update_sub_task(sub_task_id: int, payload: SubTaskUpdate, db: Session = Depends(get_db)):
    sub_task = db.query(SubTask).filter(SubTask.id == sub_task_id).first()
    if not sub_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub task not found")

    updates = payload.model_dump(exclude_unset=True)

    if "main_task_id" in updates:
        ensure_main_task_exists(db, updates["main_task_id"])
    if "slug" in updates:
        ensure_sub_task_slug_is_unique(db, updates["slug"], current_sub_task_id=sub_task.id)

    if "main_task_id" in updates:
        sub_task.main_task_id = updates["main_task_id"]
    if "title" in updates:
        sub_task.title = updates["title"]
    if "slug" in updates:
        sub_task.slug = updates["slug"]
    if "description" in updates:
        sub_task.description = updates["description"]
    if "status" in updates:
        sub_task.status = updates["status"]
    if "assign_to" in updates:
        sub_task.assign_to = updates["assign_to"]
    if "due_date" in updates:
        sub_task.due_date = updates["due_date"]

    db.commit()
    db.refresh(sub_task)
    return sub_task


@router.delete("/{sub_task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sub_task(sub_task_id: int, db: Session = Depends(get_db)):
    sub_task = db.query(SubTask).filter(SubTask.id == sub_task_id).first()
    if not sub_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sub task not found")

    db.delete(sub_task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
