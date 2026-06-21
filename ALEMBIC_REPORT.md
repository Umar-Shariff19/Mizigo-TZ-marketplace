# Alembic Report

## Summary

Schema management has been transitioned to Alembic. The FastAPI application no longer creates database tables during startup with `Base.metadata.create_all()`.

## Changes Made

- Removed `Base.metadata.create_all(bind=engine)` from `app/main.py`.
- Removed the now-unused `Base` and `engine` imports from `app/main.py`.
- Kept existing Alembic configuration in `alembic.ini`.
- Kept migration environment in `alembic/env.py`.
- Kept the initial schema migration in `alembic/versions/0001_initial_schema.py`.

## Source Of Truth

Alembic migrations are now the source of truth for database schema changes.

Use:

```bash
alembic upgrade head
```

or with Docker Compose:

```bash
docker compose run --rm api alembic upgrade head
```

## Compatibility Notes

- Existing SQLAlchemy model definitions were not redesigned.
- Existing database schema behavior was preserved.
- No new tables or columns were added for this transition.
- The app now expects migrations to be applied before serving API traffic.
