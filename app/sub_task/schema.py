from pydantic import BaseModel, ConfigDict


class SubTaskBase(BaseModel):
    main_task_id: int
    title: str
    slug: str
    description: str | None = None
    about: str | None = None
    due_date: str | None = None
    created_date: str | None = None
    updated_date: str | None = None
    assign_to: str | None = None


class SubTaskCreate(SubTaskBase):
    pass


class SubTaskUpdate(BaseModel):
    main_task_id: int | None = None
    title: str | None = None
    slug: str | None = None
    description: str | None = None
    about: str | None = None
    due_date: str | None = None
    created_date: str | None = None
    updated_date: str | None = None
    assign_to: str | None = None


class SubTaskRead(SubTaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
