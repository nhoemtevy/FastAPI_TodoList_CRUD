# Todo List

## Structure

- `app/main.py`: FastAPI application entrypoint
- `app/main_task/`: main task domain
- `app/sub_task/`: sub task domain
- `main.py`: local development runner with auto-reload

## Start

Run either command below for development with reload:

```bash
python main.py
```

```bash
uvicorn app.main:app --reload
```
