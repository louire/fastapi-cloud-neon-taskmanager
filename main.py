from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

# local, probare neon despues
tasks: list[dict] = []
next_id = 1


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"tasks": tasks})


@app.post("/tasks", response_class=HTMLResponse)
def create_task(request: Request, title: Annotated[str, Form()]):
    global next_id
    task = {"id": next_id, "title": title}
    tasks.append(task)
    next_id += 1
    return templates.TemplateResponse(request, "_task.html", {"task": task})


@app.delete("/tasks/{task_id}", response_class=HTMLResponse)
def delete_task(task_id: int):
    tasks[:] = [t for t in tasks if t["id"] != task_id]
    return ""
