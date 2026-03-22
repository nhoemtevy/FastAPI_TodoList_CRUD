from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.init_db import init_db
from app.main_task.router import router as main_task_router
from app.sub_task.router import router as sub_task_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(main_task_router)
app.include_router(sub_task_router)


@app.get("/")
def root():
    return {"message": "Hello from FastAPI"}
