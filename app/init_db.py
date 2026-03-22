from app.database import Base, engine
from app.main_task.model import MainTask
from app.sub_task.model import SubTask


def init_db():
    Base.metadata.create_all(bind=engine)
