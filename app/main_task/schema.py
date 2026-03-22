from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.sub_task.schema import SubTaskRead


class MainTaskBase(BaseModel):
    title: str
    slug: str
    description: str | None = None
    status: str = "pending"
    assign_to: str | None = None
    due_date: datetime | None = None


class MainTaskCreate(MainTaskBase):
    pass


class MainTaskUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    status: str | None = None
    assign_to: str | None = None
    due_date: datetime | None = None


class MainTaskRead(MainTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class MainTaskWithSubTasks(MainTaskRead):
    sub_tasks: list[SubTaskRead] = Field(default_factory=list)
