# Mizigo Deployment & Production Guide

## 1. Production Configuration Checklist

Before deploying to staging or production:

1. **Set `ENVIRONMENT=production`** in `.env`.
2. **Generate a Cryptographically Strong `SECRET_KEY`**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Paste the 64-character hex string into `SECRET_KEY`. The backend will refuse to start if a default or short secret is used in production mode.
3. **Configure Allowed CORS Origins**:
   ```env
   CORS_ORIGINS=https://yourmarketplacedomain.com,https://admin.yourmarketplacedomain.com
   ```
4. **Configure Database Connection**:
   ```env
   DATABASE_URL=postgresql://<prod_user>:<prod_password>@<db_host>:5432/<prod_dbname>
   ```

---

## 2. Docker & Container Deployment

### 2.1 Building the Production Image
```bash
docker build -t mizigo-backend:latest .
```

### 2.2 Running with Docker Compose (Local/Staging)
```bash
# Start database and API
docker compose up -d

# Check service health
docker compose ps
```

### 2.3 Running Database Migrations in Container
```bash
docker compose exec api alembic upgrade head
```

### 2.4 Bootstrapping the Initial Administrator Account
```bash
docker compose exec api python -m app.scripts.create_admin --email admin@mizigo.com --password "SecureInitialPassword123!"
```

---

## 3. Health Checks & Monitoring

- **Health Endpoint**: `GET /health`
  - Returns `{"status": "ok"}` with HTTP 200.
  - Suitable for AWS Target Group, Kubernetes liveness/readiness probes, or Nginx upstream health checks.

---

## 4. Backup & Disaster Recovery

### Automated PostgreSQL Backup:
```bash
pg_dump -U mizigo -d mizigo -F c -b -v -f /backups/mizigo_$(date +%Y%m%d_%H%M%S).dump
```

### Restoring from Backup:
```bash
pg_restore -U mizigo -d mizigo -v /backups/mizigo_target.dump
```
