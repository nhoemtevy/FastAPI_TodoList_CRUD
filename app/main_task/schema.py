from pydantic import BaseModel, ConfigDict, Field

from app.sub_task.schema import SubTaskRead


class MainTaskBase(BaseModel):
    title: str
    slug: str
    description: str | None = None
    about: str | None = None
    due_date: str | None = None
    created_date: str | None = None
    updated_date: str | None = None
    assign_to: str | None = None


class MainTaskCreate(MainTaskBase):
    pass


class MainTaskUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    about: str | None = None
    due_date: str | None = None
    created_date: str | None = None
    updated_date: str | None = None
    assign_to: str | None = None


class MainTaskRead(MainTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MainTaskWithSubTasks(MainTaskRead):
    sub_tasks: list[SubTaskRead] = Field(default_factory=list)
