# Mizigo Database Migration Guide

## 1. Migration Overview

Database migrations for Mizigo Marketplace are managed using **Alembic**.

- **Migration Scripts Directory**: `alembic/versions/`
- **Initial Baseline Revision**: `0001_initial_schema.py`
- **Environment Configuration**: `alembic.ini` and `alembic/env.py`

---

## 2. Fresh Database Initialization

For a brand-new installation against an empty database:

```bash
# 1. Ensure DATABASE_URL is configured in your .env
DATABASE_URL=postgresql://mizigo:mizigo@localhost:5432/mizigo

# 2. Run Alembic upgrade to apply all migrations
alembic upgrade head
```

This creates all required tables, foreign key constraints, and indexes, and stamps the revision in the `alembic_version` tracking table.

---

## 3. Handling Existing Databases (Pre-Alembic Drift)

### 3.1 The "Duplicate Table" Problem
Earlier development encountered issues where tables had been created manually or via `Base.metadata.create_all()` prior to Alembic's introduction. When `alembic upgrade head` was subsequently run, PostgreSQL raised:

`relation "users" already exists`

### 3.2 Safe Procedure for Existing Databases

Do **NOT** drop existing developer or production databases. Follow this verification sequence:

#### Step 1: Inspect Schema & Alembic Version Table
Run the following SQL check on the database:
```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
SELECT * FROM alembic_version;
```

#### Step 2: Choose the Correct Action
- **Case A: Database is completely empty**:
  Run:
  ```bash
  alembic upgrade head
  ```
- **Case B: All tables already exist and match `0001_initial_schema.py` exactly**:
  Do **NOT** run `upgrade head` (which attempts `CREATE TABLE`). Instead, record the initial revision as already applied:
  ```bash
  alembic stamp 0001_initial_schema
  ```
  *Warning: Only stamp after confirming all tables, primary keys, and foreign keys match the migration definition.*
- **Case C: Partial tables or schema differences exist**:
  1. Create a full database backup:
     ```bash
     pg_dump -U mizigo -d mizigo -F c -b -v -f mizigo_backup_pre_migration.dump
     ```
  2. Generate a targeted migration script rather than running destructive operations.

---

## 4. Creating New Migrations

When models in `app/models/` are modified:

```bash
# Generate revision script
alembic revision --autogenerate -m "describe_schema_change"

# Review the generated script in alembic/versions/ before applying!
# Verify offline SQL preview
alembic upgrade head --sql

# Apply to target database
alembic upgrade head
```

---

## 5. Rollback Procedures

To roll back the most recent migration:

```bash
# Downgrade by 1 revision
alembic downgrade -1

# Downgrade to base (empty schema)
alembic downgrade base
```
