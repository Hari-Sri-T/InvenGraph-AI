# AI Procurement - Installation Quick Reference

Choose your installation method and follow the appropriate guide.

## 🐳 Option 1: DevContainer (Recommended for Testing)

**Best for**: Quick testing, development, isolated environment

### Prerequisites
- Docker Desktop
- VS Code with Remote-Containers extension
- 8GB RAM, 10GB disk space

### Quick Start
```bash
# 1. Open in VS Code
# 2. F1 → "Dev Containers: Reopen in Container"
# 3. Wait for container to build
# 4. Run setup script
bash .devcontainer/setup_ai_procurement.sh

# 5. Start server
cd src/backend/InvenTree
invoke server
```

### Services Included
✅ PostgreSQL (automatic)
✅ Redis (automatic)
✅ Ollama (automatic)
✅ InvenTree (automatic)

### Documentation
📖 `src/backend/InvenTree/ai_procurement/DEVCONTAINER_QUICKSTART.md`

---

## 💻 Option 2: Native Installation

**Best for**: Production, custom setup, performance

### Prerequisites
- Python 3.10 or 3.11
- PostgreSQL 13+
- Redis 6.0+
- Ollama
- 8GB RAM, 10GB disk space

### Quick Start

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv postgresql redis-server curl git
```

**macOS:**
```bash
brew install python@3.11 postgresql@15 redis curl git
brew services start postgresql@15
brew services start redis
```

#### 2. Install Ollama
```bash
# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# macOS
brew install ollama

# Start Ollama
ollama serve &

# Pull llama3 model
ollama pull llama3
```

#### 3. Setup Database
```bash
# Create PostgreSQL database
sudo -u postgres psql << EOF
CREATE DATABASE inventree;
CREATE USER inventree_user WITH PASSWORD 'inventree_password';
GRANT ALL PRIVILEGES ON DATABASE inventree TO inventree_user;
\q
EOF
```

#### 4. Setup InvenTree
```bash
# Create virtual environment
cd src/backend/InvenTree
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r ai_procurement/requirements.txt

# Configure database (create dev/config.yaml)
# See NATIVE_INSTALLATION.md for config details

# Run migrations
python manage.py migrate
python manage.py migrate ai_procurement

# Create superuser
python manage.py createsuperuser
```

#### 5. Set Environment Variables
```bash
# Create .env file
cat > .env << EOF
INVENTREE_DB_ENGINE=postgresql
INVENTREE_DB_NAME=inventree
INVENTREE_DB_HOST=localhost
INVENTREE_DB_USER=inventree_user
INVENTREE_DB_PASSWORD=inventree_password
AI_PROCUREMENT_OLLAMA_URL=http://localhost:11434/api/generate
AI_PROCUREMENT_PRICE_WEIGHT=0.4
AI_PROCUREMENT_LEAD_TIME_WEIGHT=0.3
AI_PROCUREMENT_RELIABILITY_WEIGHT=0.3
EOF

# Load variables
export $(cat .env | xargs)
```

#### 6. Start Services
```bash
# Terminal 1: Ollama (if not running)
ollama serve

# Terminal 2: InvenTree
cd src/backend/InvenTree
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000

# Terminal 3 (optional): Celery worker
celery -A InvenTree worker -l info
```

### Documentation
📖 `src/backend/InvenTree/ai_procurement/NATIVE_INSTALLATION.md`

---

## 🧪 Testing (Both Methods)

### 1. Access Admin
```
http://localhost:8000/admin
```

### 2. Create Test Data
- Create a part with minimum stock = 10
- Add 2-3 suppliers with different prices
- Create stock item with quantity > 10

### 3. Get API Token
```bash
python manage.py drf_create_token <username>
```

### 4. Trigger Pipeline
```bash
curl -X POST http://localhost:8000/api/ai/procurement/pipeline/trigger/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"part_id": 1}'
```

### 5. Check Status
```bash
curl http://localhost:8000/api/ai/procurement/pipeline/status/?part_id=1 \
  -H "Authorization: Token YOUR_TOKEN"
```

### 6. View Approvals
```bash
curl http://localhost:8000/api/ai/procurement/approvals/ \
  -H "Authorization: Token YOUR_TOKEN"
```

### Testing Checklist
📋 `TESTING_CHECKLIST.md`

---

## 🔧 Common Commands

### Check Services

**DevContainer:**
```bash
docker ps | grep -E "ollama|postgres|redis"
```

**Native:**
```bash
# PostgreSQL
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Redis
redis-cli ping

# Ollama
curl http://localhost:11434/api/tags
```

### Django Management
```bash
# Migrations
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement

# Shell
python manage.py shell

# Create superuser
python manage.py createsuperuser
```

### Database Access
```bash
# DevContainer
psql -U inventree_user -d inventree -h db

# Native
psql -U inventree_user -d inventree -h localhost
```

### View Logs

**DevContainer:**
```bash
# Server logs
tail -f /home/inventree/dev/logs/inventree.log

# Ollama logs
docker logs inventree-ollama-1
```

**Native:**
```bash
# Server logs (in terminal where runserver is running)
# Or check dev/logs/inventree.log

# Ollama logs
journalctl -u ollama -f  # If installed as service
```

---

## 🐛 Troubleshooting

### Ollama Not Accessible

**DevContainer:**
```bash
docker ps | grep ollama
docker logs inventree-ollama-1
curl http://ollama:11434/api/tags
```

**Native:**
```bash
# Check if running
pgrep ollama

# Start if not running
ollama serve &

# Test
curl http://localhost:11434/api/tags
```

### Database Connection Failed

**DevContainer:**
```bash
# Check database container
docker ps | grep postgres
docker logs inventree-db-1
```

**Native:**
```bash
# Check PostgreSQL
sudo systemctl status postgresql
psql -U inventree_user -d inventree -h localhost

# Check credentials in config.yaml or .env
```

### Migration Errors

**Both:**
```bash
# Reset migrations
python manage.py migrate ai_procurement zero
python manage.py migrate ai_procurement

# Or recreate
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement
```

### Import Errors

**Both:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
pip install -r ai_procurement/requirements.txt
```

---

## 📚 Documentation Index

### Getting Started
- 🚀 **DevContainer**: `src/backend/InvenTree/ai_procurement/DEVCONTAINER_QUICKSTART.md`
- 💻 **Native**: `src/backend/InvenTree/ai_procurement/NATIVE_INSTALLATION.md`
- 📋 **Testing**: `TESTING_CHECKLIST.md`

### Reference
- 📖 **Overview**: `AI_PROCUREMENT_FINAL_README.md`
- 🔍 **Testing Guide**: `src/backend/InvenTree/ai_procurement/TESTING.md`
- 📊 **Status**: `src/backend/InvenTree/ai_procurement/IMPLEMENTATION_STATUS.md`
- ✅ **Summary**: `src/backend/InvenTree/ai_procurement/COMPLETION_SUMMARY.md`

### Technical
- 🏗️ **Architecture**: `src/backend/InvenTree/ai_procurement/README.md`
- 📐 **Design**: `.kiro/specs/agentic-ai-inventory/design.md`
- 📋 **Requirements**: `.kiro/specs/agentic-ai-inventory/requirements.md`
- ✓ **Tasks**: `.kiro/specs/agentic-ai-inventory/tasks.md`

---

## 🎯 Quick Decision Guide

**Choose DevContainer if:**
- ✅ You want to test quickly
- ✅ You don't want to install services manually
- ✅ You're developing/testing features
- ✅ You want isolated environment
- ✅ You have Docker Desktop

**Choose Native if:**
- ✅ You're deploying to production
- ✅ You need custom configuration
- ✅ You want better performance
- ✅ You already have services installed
- ✅ You don't have Docker Desktop

---

## 🆘 Getting Help

1. **Check logs** (see commands above)
2. **Review error messages** in terminal
3. **Check service status** (PostgreSQL, Redis, Ollama)
4. **Verify configuration** (config.yaml or .env)
5. **Check documentation** (see index above)
6. **Test services individually**:
   ```bash
   # PostgreSQL
   psql -U inventree_user -d inventree -h localhost -c "SELECT 1;"
   
   # Redis
   redis-cli ping
   
   # Ollama
   curl http://localhost:11434/api/tags
   ```

---

## ⚡ Performance Tips

### DevContainer
- Allocate at least 8GB RAM to Docker
- Use SSD for Docker volumes
- Close unnecessary applications

### Native
- Tune PostgreSQL (see NATIVE_INSTALLATION.md)
- Configure Redis maxmemory
- Use GPU for Ollama if available
- Enable Celery for async processing

---

## 🎉 Success Indicators

You're ready to test when:
- ✅ Server starts without errors
- ✅ Admin interface accessible
- ✅ All 10 AI procurement models visible in admin
- ✅ Ollama responds to API calls
- ✅ Database connection works
- ✅ Redis connection works

---

**Need more details?** See the full installation guides linked above.

**Ready to test?** Follow `TESTING_CHECKLIST.md`

**Questions?** Check the troubleshooting sections in the installation guides.
