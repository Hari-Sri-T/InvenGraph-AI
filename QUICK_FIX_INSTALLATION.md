# Quick Fix - Correct Installation Steps

## The Issue

The requirements.txt file is in `src/backend/requirements.txt`, not in `src/backend/InvenTree/requirements.txt`.

## Correct Installation Steps

### From Your Current Location

You're currently in: `~/Professional/Projects/InvenTree/src/backend/InvenTree`

```bash
# 1. Go back to backend directory
cd ..

# 2. Install InvenTree dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Go to InvenTree directory
cd InvenTree

# 4. Install AI Procurement dependencies
pip install -r ai_procurement/requirements.txt

# 5. Now you can run migrations and start the server
python manage.py migrate
python manage.py migrate ai_procurement
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

## Complete Fresh Start (If Needed)

If you want to start completely fresh:

```bash
# 1. Go to project root
cd ~/Professional/Projects/InvenTree

# 2. Create virtual environment in backend directory
cd src/backend
python3.11 -m venv venv
source venv/bin/activate

# 3. Install InvenTree dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install AI Procurement dependencies
cd InvenTree
pip install -r ai_procurement/requirements.txt

# 5. Configure database (if not done)
# Create dev/config.yaml or set environment variables
# See NATIVE_INSTALLATION.md for database setup

# 6. Run migrations
python manage.py migrate
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement

# 7. Create superuser
python manage.py createsuperuser

# 8. Start server
python manage.py runserver 0.0.0.0:8000
```

## Directory Structure Clarification

```
InvenTree/
├── src/
│   ├── backend/
│   │   ├── requirements.txt          ← InvenTree dependencies HERE
│   │   ├── venv/                     ← Create venv HERE
│   │   └── InvenTree/                ← Django project directory
│   │       ├── manage.py
│   │       ├── InvenTree/            ← Settings directory
│   │       └── ai_procurement/
│   │           └── requirements.txt  ← AI Procurement dependencies HERE
│   └── frontend/
```

## Quick Commands Reference

### If you're in `src/backend/InvenTree`:
```bash
# Install InvenTree deps
cd .. && pip install -r requirements.txt && cd InvenTree

# Install AI Procurement deps
pip install -r ai_procurement/requirements.txt

# Run migrations
python manage.py migrate
python manage.py migrate ai_procurement

# Start server
python manage.py runserver
```

### If you're in project root:
```bash
# Install all dependencies
cd src/backend
pip install -r requirements.txt
cd InvenTree
pip install -r ai_procurement/requirements.txt

# Run migrations
python manage.py migrate
python manage.py migrate ai_procurement

# Start server
python manage.py runserver
```

## Verify Installation

After installing dependencies, verify:

```bash
# Check Prophet
python -c "import prophet; print('Prophet OK')"

# Check LangGraph
python -c "import langgraph; print('LangGraph OK')"

# Check Django
python -c "import django; print('Django OK')"

# Check all AI procurement imports
python -c "from ai_procurement.agents.demand_agent import DemandAgent; print('AI Procurement OK')"
```

## Common Issues

### Issue: "No module named 'prophet'"
**Solution**: Make sure you installed `ai_procurement/requirements.txt`
```bash
cd src/backend/InvenTree
pip install -r ai_procurement/requirements.txt
```

### Issue: "No module named 'django'"
**Solution**: Make sure you installed InvenTree's `requirements.txt`
```bash
cd src/backend
pip install -r requirements.txt
```

### Issue: Virtual environment not activated
**Solution**: Activate it
```bash
cd src/backend
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Issue: Wrong Python version
**Solution**: Use Python 3.10 or 3.11
```bash
python3.11 -m venv venv
source venv/bin/activate
```

## Next Steps

Once dependencies are installed:

1. **Setup Database** (if not done)
   - See `NATIVE_INSTALLATION.md` for PostgreSQL setup

2. **Configure Environment**
   - Create `dev/config.yaml` or `.env` file
   - See `NATIVE_INSTALLATION.md` for configuration

3. **Run Migrations**
   ```bash
   python manage.py migrate
   python manage.py migrate ai_procurement
   ```

4. **Create Superuser**
   ```bash
   python manage.py createsuperuser
   ```

5. **Start Server**
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

6. **Test the System**
   - Follow `TESTING_CHECKLIST.md`

## Still Having Issues?

Check:
1. Virtual environment is activated (you should see `(venv)` in prompt)
2. You're in the correct directory
3. Python version is 3.10 or 3.11: `python --version`
4. All system dependencies are installed (PostgreSQL, Redis, etc.)

For more help, see:
- `NATIVE_INSTALLATION.md` - Full installation guide
- `INSTALLATION_QUICK_REFERENCE.md` - Quick reference
- `FINAL_HANDOFF.md` - Complete overview
