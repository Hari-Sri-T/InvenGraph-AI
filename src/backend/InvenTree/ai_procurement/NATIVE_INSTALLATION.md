# AI Procurement - Native Installation Guide

This guide explains how to run the AI Procurement system without using DevContainer (native installation on your machine).

## System Requirements

- **OS**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows (WSL2)
- **Python**: 3.10 or 3.11
- **PostgreSQL**: 13+
- **Redis**: 6.0+
- **RAM**: At least 8GB
- **Disk Space**: At least 10GB free (for Ollama models)

## Prerequisites

### 1. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y \
    python3.11 python3.11-dev python3.11-venv \
    postgresql postgresql-contrib \
    redis-server \
    libpq-dev \
    libldap2-dev libsasl2-dev \
    libpango1.0-0 libcairo2 \
    poppler-utils \
    curl \
    git
```

#### macOS (using Homebrew)
```bash
brew install python@3.11 postgresql@15 redis curl git
brew services start postgresql@15
brew services start redis
```

#### Windows (WSL2)
Follow Ubuntu instructions above in WSL2 terminal.

### 2. Install Ollama

#### Linux
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### macOS
```bash
brew install ollama
```

#### Windows
Download from https://ollama.ai/download/windows

### 3. Start Ollama Service

```bash
# Linux/macOS
ollama serve

# Or run in background
nohup ollama serve > /dev/null 2>&1 &
```

### 4. Pull llama3 Model

```bash
ollama pull llama3
```

This will download ~4.7GB. Wait for completion.

### 5. Verify Ollama

```bash
curl http://localhost:11434/api/tags
```

Should return JSON with llama3 model listed.

## InvenTree Setup

### 1. Clone InvenTree (if not already done)

```bash
git clone https://github.com/inventree/InvenTree.git
cd InvenTree
```

### 2. Create Python Virtual Environment

```bash
# Create venv in the backend directory (not InvenTree subdirectory)
cd src/backend
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install InvenTree Dependencies

```bash
# Install InvenTree dependencies (you should be in src/backend)
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install AI Procurement Dependencies

```bash
# Go to InvenTree directory and install AI procurement dependencies
cd InvenTree
pip install -r ai_procurement/requirements.txt
```

```bash
# Install AI procurement specific dependencies
pip install -r ai_procurement/requirements.txt
```

## Database Setup

### 1. Create PostgreSQL Database

```bash
# Start PostgreSQL (if not running)
sudo systemctl start postgresql  # Linux
# or
brew services start postgresql@15  # macOS

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE inventree;
CREATE USER inventree_user WITH PASSWORD 'inventree_password';
ALTER ROLE inventree_user SET client_encoding TO 'utf8';
ALTER ROLE inventree_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE inventree_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE inventree TO inventree_user;
\q
EOF
```

### 2. Configure InvenTree Database

Create or edit `dev/config.yaml`:

```yaml
# Database settings
database:
  ENGINE: postgresql
  NAME: inventree
  USER: inventree_user
  PASSWORD: inventree_password
  HOST: localhost
  PORT: 5432

# Cache settings
cache:
  host: localhost
  port: 6379

# Debug mode
debug: true

# Plugins
plugins_enabled: true

# Site URL
site_url: http://localhost:8000

# CORS
cors:
  allow_all: true
```

### 3. Run Migrations

```bash
# Make sure you're in src/backend/InvenTree with venv activated
python manage.py makemigrations
python manage.py migrate
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement
```

### 4. Create Superuser

```bash
python manage.py createsuperuser
```

Follow prompts to create admin account.

## Environment Variables

Create a `.env` file in `src/backend/InvenTree/`:

```bash
# Database
INVENTREE_DB_ENGINE=postgresql
INVENTREE_DB_NAME=inventree
INVENTREE_DB_HOST=localhost
INVENTREE_DB_USER=inventree_user
INVENTREE_DB_PASSWORD=inventree_password
INVENTREE_DB_PORT=5432

# Cache
INVENTREE_CACHE_HOST=localhost
INVENTREE_CACHE_PORT=6379

# Debug
INVENTREE_DEBUG=True

# Plugins
INVENTREE_PLUGINS_ENABLED=True

# Site
INVENTREE_SITE_URL=http://localhost:8000

# CORS
INVENTREE_CORS_ORIGIN_ALLOW_ALL=True

# AI Procurement Configuration
AI_PROCUREMENT_OLLAMA_URL=http://localhost:11434/api/generate
AI_PROCUREMENT_PRICE_WEIGHT=0.4
AI_PROCUREMENT_LEAD_TIME_WEIGHT=0.3
AI_PROCUREMENT_RELIABILITY_WEIGHT=0.3
AI_PROCUREMENT_FORECAST_DAYS=30
AI_PROCUREMENT_APPROVAL_TIMEOUT_DAYS=7
AI_PROCUREMENT_EMA_ALPHA=0.3
AI_PROCUREMENT_PROPHET_CACHE_TTL_DAYS=7
```

Load environment variables:

```bash
# Linux/macOS
export $(cat .env | xargs)

# Or add to your shell profile (~/.bashrc or ~/.zshrc)
source .env
```

## Start Services

### 1. Start Redis (if not running)

```bash
# Linux
sudo systemctl start redis

# macOS
brew services start redis

# Or run manually
redis-server
```

### 2. Start Ollama (if not running)

```bash
ollama serve
```

### 3. Start InvenTree Server

```bash
# Make sure you're in src/backend/InvenTree with venv activated
python manage.py runserver 0.0.0.0:8000
```

Server will be available at http://localhost:8000

### 4. (Optional) Start Celery Worker

In a separate terminal:

```bash
cd src/backend/InvenTree
source venv/bin/activate
celery -A InvenTree worker -l info
```

### 5. (Optional) Start Celery Beat (for periodic tasks)

In another terminal:

```bash
cd src/backend/InvenTree
source venv/bin/activate
celery -A InvenTree beat -l info
```

## Frontend Setup (Optional)

If you want to run the frontend development server:

```bash
cd src/frontend
npm install
npm run dev
```

Frontend will be available at http://localhost:5173

## Verification

### 1. Check Services

```bash
# PostgreSQL
psql -U inventree_user -d inventree -h localhost -c "SELECT 1;"

# Redis
redis-cli ping

# Ollama
curl http://localhost:11434/api/tags

# InvenTree
curl http://localhost:8000/api/
```

### 2. Access Admin Interface

Open http://localhost:8000/admin and log in with your superuser credentials.

### 3. Verify AI Procurement Models

In admin, you should see the "Ai Procurement" section with all 10 models.

## Testing the System

### 1. Create Test Data

Follow the same steps as in DEVCONTAINER_QUICKSTART.md:
- Create a test part with minimum stock
- Add 2-3 suppliers
- Create stock items

### 2. Get API Token

```bash
python manage.py drf_create_token <your_username>
```

### 3. Test Pipeline Trigger

```bash
curl -X POST http://localhost:8000/api/ai/procurement/pipeline/trigger/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"part_id": 1}'
```

### 4. Check Pipeline Status

```bash
curl http://localhost:8000/api/ai/procurement/pipeline/status/?part_id=1 \
  -H "Authorization: Token YOUR_TOKEN"
```

### 5. View Approvals

```bash
curl http://localhost:8000/api/ai/procurement/approvals/ \
  -H "Authorization: Token YOUR_TOKEN"
```

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Check connection
psql -U inventree_user -d inventree -h localhost

# If connection refused, check pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf  # Linux
# Add: host all all 127.0.0.1/32 md5
sudo systemctl restart postgresql
```

### Redis Connection Issues

```bash
# Check if Redis is running
redis-cli ping

# Start Redis
sudo systemctl start redis  # Linux
brew services start redis  # macOS
```

### Ollama Issues

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check logs
journalctl -u ollama -f  # Linux (if installed as service)
```

### Python Import Errors

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
pip install -r ai_procurement/requirements.txt
```

### Migration Errors

```bash
# Reset AI procurement migrations
python manage.py migrate ai_procurement zero
python manage.py migrate ai_procurement

# Or reset entire database (WARNING: deletes all data)
python manage.py flush
python manage.py migrate
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # Linux/macOS
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>

# Or use different port
python manage.py runserver 0.0.0.0:8001
```

## Performance Optimization

### 1. PostgreSQL Tuning

Edit `postgresql.conf`:

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
```

Restart PostgreSQL after changes.

### 2. Redis Tuning

Edit `redis.conf`:

```ini
maxmemory 256mb
maxmemory-policy allkeys-lru
```

Restart Redis after changes.

### 3. Ollama Performance

```bash
# Use GPU if available (NVIDIA)
ollama serve --gpu

# Adjust context window
ollama run llama3 --ctx-size 4096
```

## Production Deployment

For production deployment, consider:

1. **Use Gunicorn/uWSGI** instead of `runserver`
2. **Use Nginx** as reverse proxy
3. **Enable HTTPS** with SSL certificates
4. **Use systemd services** for auto-start
5. **Set up monitoring** (Prometheus, Grafana)
6. **Configure backups** for database and models
7. **Use environment-specific configs**
8. **Enable security features** (see IMPLEMENTATION_STATUS.md)

## Useful Commands

### Django Management

```bash
# Create migrations
python manage.py makemigrations ai_procurement

# Apply migrations
python manage.py migrate ai_procurement

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Create superuser
python manage.py createsuperuser
```

### Database Management

```bash
# Backup database
pg_dump -U inventree_user inventree > backup.sql

# Restore database
psql -U inventree_user inventree < backup.sql

# Access database
psql -U inventree_user -d inventree
```

### Celery Management

```bash
# Start worker
celery -A InvenTree worker -l info

# Start beat scheduler
celery -A InvenTree beat -l info

# Monitor tasks
celery -A InvenTree inspect active

# Purge all tasks
celery -A InvenTree purge
```

### Ollama Management

```bash
# List models
ollama list

# Pull model
ollama pull llama3

# Remove model
ollama rm llama3

# Show model info
ollama show llama3
```

## Development Workflow

1. **Activate virtual environment**
   ```bash
   source venv/bin/activate
   ```

2. **Start all services**
   ```bash
   # Terminal 1: PostgreSQL (if not running as service)
   # Terminal 2: Redis (if not running as service)
   # Terminal 3: Ollama
   ollama serve
   
   # Terminal 4: InvenTree
   python manage.py runserver
   
   # Terminal 5: Celery worker (optional)
   celery -A InvenTree worker -l info
   ```

3. **Make changes to code**

4. **Test changes**
   ```bash
   python manage.py test ai_procurement
   ```

5. **Create migrations if models changed**
   ```bash
   python manage.py makemigrations ai_procurement
   python manage.py migrate ai_procurement
   ```

## Getting Help

- Check logs: `tail -f dev/logs/inventree.log`
- Django shell: `python manage.py shell`
- Database queries: `psql -U inventree_user -d inventree`
- Check service status: `systemctl status <service>`
- Review error messages in terminal

## Next Steps

Once everything is running:

1. Follow the testing guide: `TESTING.md`
2. Create test data as described above
3. Test the pipeline execution
4. Review the implementation: `IMPLEMENTATION_STATUS.md`
5. Check the API documentation: `README.md`

## Quick Start Script

Save this as `start_ai_procurement.sh`:

```bash
#!/bin/bash

# Start AI Procurement System

echo "Starting AI Procurement System..."

# Check if services are running
if ! pgrep -x "postgres" > /dev/null; then
    echo "Starting PostgreSQL..."
    sudo systemctl start postgresql
fi

if ! pgrep -x "redis-server" > /dev/null; then
    echo "Starting Redis..."
    sudo systemctl start redis
fi

if ! pgrep -x "ollama" > /dev/null; then
    echo "Starting Ollama..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 2
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
export $(cat .env | xargs)

# Start InvenTree
echo "Starting InvenTree server..."
python manage.py runserver 0.0.0.0:8000
```

Make it executable:
```bash
chmod +x start_ai_procurement.sh
./start_ai_procurement.sh
```

Happy coding! 🚀
