import os
import tempfile
import unittest
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite://"

from app.database import Base, create_db_engine
from app.init_db import init_db
from app.main_task.router import (
    create_main_task,
    delete_main_task,
    get_main_task,
    list_main_tasks,
    update_main_task,
)
from app.main_task.schema import MainTaskCreate, MainTaskUpdate
from app.sub_task.router import create_sub_task, list_sub_tasks
from app.sub_task.schema import SubTaskCreate


class TodoApiSpecTestCase(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.engine = create_db_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        init_db(bind=self.engine)
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_main_task_and_sub_task_crud_shape(self):
        main_task = create_main_task(
            MainTaskCreate(
                title="Build API",
                slug="build-api",
                description="Create the todo API",
                status="pending",
                assign_to="tevy",
                due_date=datetime(2026, 3, 30, tzinfo=timezone.utc),
            ),
            db=self.db,
        )

        self.assertEqual(main_task.status, "pending")
        self.assertEqual(main_task.assign_to, "tevy")
        self.assertIsNotNone(main_task.created_at)
        self.assertIsNotNone(main_task.updated_at)

        sub_task = create_sub_task(
            SubTaskCreate(
                main_task_id=main_task.id,
                title="Add routes",
                slug="add-routes",
                description="Implement CRUD",
                status="in_progress",
                assign_to="tevy",
                due_date=datetime(2026, 3, 28, tzinfo=timezone.utc),
            ),
            db=self.db,
        )

        self.assertEqual(sub_task.main_task_id, main_task.id)
        self.assertEqual(sub_task.status, "in_progress")

        task_with_children = get_main_task(main_task.id, db=self.db)
        self.assertEqual(len(task_with_children.sub_tasks), 1)
        self.assertEqual(task_with_children.sub_tasks[0].slug, "add-routes")

        updated_task = update_main_task(
            main_task.id,
            MainTaskUpdate(status="completed", assign_to="team"),
            db=self.db,
        )
        self.assertEqual(updated_task.status, "completed")
        self.assertEqual(updated_task.assign_to, "team")

        delete_response = delete_main_task(main_task.id, db=self.db)
        self.assertEqual(delete_response.status_code, 204)
        self.assertEqual(
            list_main_tasks(
                status_filter=None,
                assign_to=None,
                slug=None,
                skip=0,
                limit=10,
                db=self.db,
            ),
            [],
        )

    def test_list_endpoints_support_filters_and_pagination(self):
        first_task = create_main_task(
            MainTaskCreate(
                title="Task One",
                slug="task-one",
                description="First",
                status="pending",
                assign_to="alpha",
            ),
            db=self.db,
        )
        second_task = create_main_task(
            MainTaskCreate(
                title="Task Two",
                slug="task-two",
                description="Second",
                status="completed",
                assign_to="beta",
            ),
            db=self.db,
        )

        create_sub_task(
            SubTaskCreate(
                main_task_id=first_task.id,
                title="Sub One",
                slug="sub-one",
                description="First sub task",
                status="pending",
                assign_to="alpha",
            ),
            db=self.db,
        )
        create_sub_task(
            SubTaskCreate(
                main_task_id=second_task.id,
                title="Sub Two",
                slug="sub-two",
                description="Second sub task",
                status="completed",
                assign_to="beta",
            ),
            db=self.db,
        )

        filtered_main_tasks = list_main_tasks(
            status_filter="completed",
            assign_to=None,
            slug=None,
            skip=0,
            limit=10,
            db=self.db,
        )
        self.assertEqual([task.slug for task in filtered_main_tasks], ["task-two"])

        paginated_main_tasks = list_main_tasks(
            status_filter=None,
            assign_to=None,
            slug=None,
            skip=1,
            limit=1,
            db=self.db,
        )
        self.assertEqual([task.slug for task in paginated_main_tasks], ["task-two"])

        filtered_sub_tasks = list_sub_tasks(
            main_task_id=second_task.id,
            status_filter="completed",
            assign_to=None,
            slug=None,
            skip=0,
            limit=10,
            db=self.db,
        )
        self.assertEqual([sub_task.slug for sub_task in filtered_sub_tasks], ["sub-two"])

        paginated_sub_tasks = list_sub_tasks(
            main_task_id=None,
            status_filter=None,
            assign_to=None,
            slug=None,
            skip=1,
            limit=1,
            db=self.db,
        )
        self.assertEqual([sub_task.slug for sub_task in paginated_sub_tasks], ["sub-two"])


if __name__ == "__main__":
    unittest.main()
