# Mizigo Backend

FastAPI backend for the Mizigo marketplace.

## Stack

- FastAPI
- SQLAlchemy ORM
- PostgreSQL
- JWT authentication
- Alembic migrations
- Docker Compose for local services

## Local Setup

1. Create and activate a Python virtual environment.

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create your local environment file.

```bash
copy .env.example .env
```

4. Update `.env` as needed.

For local Docker Compose, use:

```env
DATABASE_URL=postgresql://mizigo:mizigo@db:5432/mizigo
```

For a host PostgreSQL database, use:

```env
DATABASE_URL=postgresql://mizigo:mizigo@localhost:5432/mizigo
```

## Run With Docker Compose

```bash
docker compose up --build
```

API:

```text
http://localhost:8000
```

Swagger docs:

```text
http://localhost:8000/docs
```

## Run Migrations

With local Python:

```bash
alembic upgrade head
```

With Docker Compose:

```bash
docker compose run --rm api alembic upgrade head
```

## Run The API Locally

```bash
uvicorn app.main:app --reload
```

## Run Tests

```bash
pytest
```

## Notes

- Existing endpoint URLs are preserved.
- Existing order, inventory, payment, and authentication behavior is preserved.
- `Base.metadata.create_all(bind=engine)` is still present for compatibility with the current app startup behavior. Alembic is now available for controlled migrations going forward.
