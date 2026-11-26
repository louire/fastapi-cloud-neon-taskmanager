# fastapi-cloud-neon-taskmanager

A minimal task manager for learning FastAPI, FastAPI Cloud, Neon, htmx and uv.

## Stack

- **FastAPI**: the backend, which also serves the HTML with Jinja2.
- **htmx**: creating and deleting tasks without writing JavaScript.
- **SQLModel + psycopg**: database access.
- **Neon**: Postgres in production, connected through the FastAPI Cloud integration.
- **FastAPI Cloud**: deployment.
- **uv**: Python dependencies and environment.

## What I tried

1. I started with a **Next + Bun** frontend. I dropped it because, for something this simple, it meant two apps and two deployments.
2. I considered **htmx on GitHub Pages**, with the API on FastAPI Cloud. It works, but it requires setting up CORS and cross-domain cookies.
3. I settled on **htmx served by FastAPI itself**: one project, one domain and no build step.
4. Tasks moved from an in-memory list to **Neon**. The table is created automatically when the app starts.

## Run it locally

```bash
uv sync
uv run fastapi dev
```

Open http://localhost:8000. Without `DATABASE_URL`, the app uses a local SQLite file (`tasks.db`).

To use Neon locally:

```bash
export DATABASE_URL="postgresql://..."
uv run fastapi dev
```

## Deploy

```bash
uv run fastapi deploy
```

FastAPI Cloud injects `DATABASE_URL` from the Neon integration.

## How it works

The app is a single page where you can add and delete tasks. Everything runs in one FastAPI app, with no separate frontend:

1. `GET /` reads all tasks from the database and renders `templates/index.html`.
2. Submitting the form makes htmx send `POST /tasks`. FastAPI saves the task and returns only its `<li>` (`templates/_task.html`), which htmx appends to the list without reloading the page.
3. Clicking ✕ makes htmx send `DELETE /tasks/{id}`. FastAPI deletes the task and returns an empty response, and htmx removes that `<li>` from the page.

The server always returns HTML instead of JSON, so the browser needs no JavaScript beyond htmx itself.
