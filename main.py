import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Field, Session, SQLModel, create_engine, select

logger = logging.getLogger(__name__)


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str


class DatabaseUnavailable(Exception):
    """No hay DATABASE_URL configurada."""


# FastAPI Cloud inyecta DATABASE_URL (Neon). En local: DATABASE_URL=sqlite:///tasks.db
database_url = os.getenv("DATABASE_URL")
engine = None
if database_url:
    # SQLAlchemy usa psycopg2 con "postgresql://"; forzamos psycopg (v3)
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    # connect_timeout: si la base ya no existe, fallar rápido en vez de colgarse
    connect_args = {"connect_timeout": 10} if database_url.startswith("postgresql") else {}
    # pool_pre_ping: Neon suspende la base cuando está inactiva y corta las conexiones
    engine = create_engine(database_url, pool_pre_ping=True, connect_args=connect_args)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Si la base no existe, la app arranca igual y muestra el aviso en vez de caerse
    if engine is None:
        logger.warning("DATABASE_URL is not set")
    else:
        try:
            SQLModel.metadata.create_all(engine)
        except SQLAlchemyError:
            logger.exception("Could not connect to the database")
    yield


def get_session():
    if engine is None:
        raise DatabaseUnavailable
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


@app.exception_handler(DatabaseUnavailable)
@app.exception_handler(SQLAlchemyError)
def database_gone(request: Request, exc: Exception):
    # Peticiones de htmx: recargar la página entera para que se vea el aviso
    if request.headers.get("HX-Request"):
        return Response(status_code=503, headers={"HX-Refresh": "true"})
    return templates.TemplateResponse(
        request, "index.html", {"db_gone": True}, status_code=503
    )


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
