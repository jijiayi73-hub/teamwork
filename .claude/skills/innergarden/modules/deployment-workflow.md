# Deployment Workflow

## Scope

Use this module for deploying Inner Garden to VPS production environment, including code updates, container rebuilds, database migrations, and deployment verification.

## VPS Configuration

- **Domain**: jijiayi.online
- **IP**: 49.232.17.105
- **System**: Ubuntu 22.04.5 LTS
- **User**: ubuntu
- **SSH**: `vps` alias (configured in `~/.ssh/config`)
- **Deploy Directory**: `/opt/inner-garden`

## Deployment Modes

Recognize these deployment scenarios:

- `quick`: Code-only changes, no dependency changes → restart containers only
- `full`: Dependency changes, new features → rebuild and restart containers
- `migration`: Database schema changes → run Alembic migrations
- `rollback`: Deployment failed → revert to previous version
- `verification`: Check deployment health → run health checks

## Local Preparation

### 1. Build Frontend (if frontend changes)

```bash
cd frontend
npm run build
```

### 2. Local Testing (recommended)

```bash
# Backend tests
cd backend
py -m pytest tests/ -v

# Frontend build test
cd frontend
npm run build
```

### 3. Git Commit (optional but recommended)

```bash
git add .
git commit -m "feat: deployment description"
git push origin <branch>
```

## Deployment Methods

### Method A: rsync (Recommended for small updates)

```bash
rsync -avz --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='dist' \
    --exclude='.pytest_cache' \
    e:/Project/teamwork/ vps:/opt/inner-garden/
```

### Method B: tar + scp (For larger updates)

```bash
cd e:/Project/teamwork
tar -czf inner-garden-update.tar.gz \
    backend/ frontend/ docker-compose.yml .env.production \
    --exclude=node_modules --exclude=__pycache__ \
    --exclude=.git --exclude=dist --exclude=*.pyc

scp inner-garden-update.tar.gz vps:/opt/
```

### Method C: Git Pull (If using Git on VPS)

```bash
ssh vps "cd /opt/inner-garden && git pull origin <branch>"
```

## VPS Deployment Commands

### Quick Update (code only, no dependencies changed)

```bash
ssh vps "cd /opt/inner-garden && docker compose restart backend frontend"
```

### Full Update (dependencies changed or new features)

```bash
# After transferring files via rsync/tar/git
ssh vps
cd /opt/inner-garden

# Ensure .env exists and is correct
ls -la .env
# If not, copy from .env.production
cp .env.production .env
# nano .env  # Update API keys if needed

# Rebuild containers
docker compose build

# Restart containers
docker compose up -d

# Run migrations (if database schema changed)
docker compose exec backend alembic upgrade head

# Check logs
docker compose logs -f
```

### If using docker-compose.prod.yml

```bash
# Build with production config
docker compose -f docker-compose.prod.yml build --no-cache
docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Verification Commands

### Health Checks

```bash
# Container status
ssh vps "cd /opt/inner-garden && docker compose ps"

# Backend health
curl https://jijiayi.online/api/v1/health

# Frontend health
curl https://jijiayi.online/health

# Check logs
ssh vps "cd /opt/inner-garden && docker compose logs -f backend"
```

### Expected Output

```json
{"success":true,"data":{"status":"healthy"},"message":"ok","request_id":"local"}
```

## Rollback Procedure

If deployment fails:

```bash
ssh vps
cd /opt/inner-garden

# Stop services
docker compose down

# Restore from backup (if exists)
cd /opt
mv inner-garden inner-garden.failed
mv inner-garden.backup.YYYYMMDD_HHMMSS inner-garden

# Restart
cd inner-garden
docker compose up -d
```

## Prohibited

- Deploying without testing locally first
- Skipping migration steps when database schema changed
- Forgetting to rebuild containers after dependency changes
- Deploying with broken container startup
- Overwriting production `.env` without backup
- Running migrations without checking current migration version

## Validation Requirements

Before marking deployment complete:

1. **Container Status**: All containers show `healthy` or `Up` status
2. **Health Endpoint**: `/api/v1/health` returns success
3. **No Errors**: Logs show no critical errors
4. **Migration Applied**: `alembic current` shows latest version

## Quick Reference

| Operation | Command |
|-----------|---------|
| View logs | `ssh vps "cd /opt/inner-garden && docker compose logs -f"` |
| Restart services | `ssh vps "cd /opt/inner-garden && docker compose restart"` |
| Stop services | `ssh vps "cd /opt/inner-garden && docker compose down"` |
| Enter container | `ssh vps "cd /opt/inner-garden && docker compose exec backend bash"` |
| Run migrations | `ssh vps "cd /opt/inner-garden && docker compose exec backend alembic upgrade head"` |
| Check migration | `ssh vps "cd /opt/inner-garden && docker compose exec backend alembic current"` |
| Container status | `ssh vps "cd /opt/inner-garden && docker compose ps"` |

## One-Click Deployment Script

For automated deployments, use:

```bash
# From local, run one-click deployment
ssh vps 'bash -s' < scripts/one-click-deploy.sh
```

This script handles:
1. Docker mirror configuration
2. Container build and startup
3. Nginx configuration
4. API key setup
5. Database migrations
6. Admin account creation
