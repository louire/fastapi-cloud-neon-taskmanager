import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Session, SQLModel, create_engine, select


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str


# FastAPI Cloud inyecta DATABASE_URL (Neon). En local, sin la variable, usa SQLite.
database_url = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
# SQLAlchemy usa psycopg2 con "postgresql://"; forzamos psycopg (v3)
database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
# pool_pre_ping: Neon suspende la base cuando está inactiva y corta las conexiones
engine = create_engine(database_url, pool_pre_ping=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.get("/", response_class=HTMLResponse)
def index(request: Request, session: SessionDep):
    tasks = session.exec(select(Task).order_by(Task.id)).all()
    return templates.TemplateResponse(request, "index.html", {"tasks": tasks})


@app.post("/tasks", response_class=HTMLResponse)
def create_task(request: Request, title: Annotated[str, Form()], session: SessionDep):
    task = Task(title=title)
    session.add(task)
    session.commit()
    session.refresh(task)
    return templates.TemplateResponse(request, "_task.html", {"task": task})


@app.delete("/tasks/{task_id}", response_class=HTMLResponse)
def delete_task(task_id: int, session: SessionDep):
    task = session.get(Task, task_id)
    if task:
        session.delete(task)
        session.commit()
    return ""
