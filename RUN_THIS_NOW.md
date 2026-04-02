# 🚀 Quick Fix - Run These Commands Now

## ⚠️ IMPORTANT: Migration Hanging Issue Fixed

If your migrations were hanging at "Skipping plugin loading sequence", this has been fixed! The issue was caused by eager database initialization. All fixes have been applied to:
- `signals.py` - Lazy imports added
- `views.py` - Lazy imports added  
- `tasks.py` - Lazy imports added + migrated from Celery to django-q2
- `state_manager.py` - Lazy checkpointer initialization + SQLite support

See `MIGRATION_FIX_SUMMARY.md` for technical details.
See `CELERY_TO_DJANGO_Q_MIGRATION.md` for task queue migration details.

## The Problem
InvenTree needs environment variables set before running migrations.

## The Solution
Run these commands in your terminal (you're already in the right directory):

```bash
# 1. Set environment variables (copy and paste all of these)
export INVENTREE_DB_ENGINE=sqlite3
export INVENTREE_DB_NAME=./dev/database.sqlite3
export INVENTREE_MEDIA_ROOT=./dev/media
export INVENTREE_STATIC_ROOT=./dev/static
export INVENTREE_BACKUP_DIR=./dev/backup
export INVENTREE_PLUGIN_DIR=./dev/plugins
export INVENTREE_CONFIG_FILE=./dev/config.yaml
export INVENTREE_SECRET_KEY_FILE=./dev/secret_key.txt
export INVENTREE_DEBUG=True
export INVENTREE_LOG_LEVEL=INFO
export INVENTREE_PLUGINS_ENABLED=True

# AI Procurement settings
export AI_PROCUREMENT_OLLAMA_URL=http://localhost:11434/api/generate
export AI_PROCUREMENT_PRICE_WEIGHT=0.4
export AI_PROCUREMENT_LEAD_TIME_WEIGHT=0.3
export AI_PROCUREMENT_RELIABILITY_WEIGHT=0.3

# 2. Now run migrations
python manage.py migrate

# 3. Create AI procurement migrations
python manage.py makemigrations ai_procurement

# 4. Apply AI procurement migrations
python manage.py migrate ai_procurement

# 5. Create superuser (follow prompts)
python manage.py createsuperuser

# 6. Start server
python manage.py runserver 0.0.0.0:8000
```

## Alternative: Use the Test Script

Test that the migration fixes work:

```bash
# From InvenTree directory (where manage.py is)
cd ~/Professional/Projects/InvenTree/src/backend/InvenTree

# Run the test script
./test_migration_fix.sh
```

This will verify that:
1. Django settings can be imported without hanging
2. The ai_procurement app can be imported
3. Signals can be imported without triggering database connections
4. Migrations run successfully without hanging

## Alternative: Use the Setup Script

Or source the setup script I created:

```bash
# From project root
cd ~/Professional/Projects/InvenTree
source setup_inventree_env.sh

# Then go to InvenTree directory
cd src/backend/InvenTree

# Run migrations
python manage.py migrate
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement

# Create superuser
python manage.py createsuperuser

# Start server
python manage.py runserver 0.0.0.0:8000
```

## Make It Permanent

To avoid setting these every time, add them to your shell profile:

```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export INVENTREE_DB_ENGINE=sqlite3' >> ~/.bashrc
echo 'export INVENTREE_DB_NAME=~/Professional/Projects/InvenTree/dev/database.sqlite3' >> ~/.bashrc
echo 'export INVENTREE_MEDIA_ROOT=~/Professional/Projects/InvenTree/dev/media' >> ~/.bashrc
echo 'export INVENTREE_STATIC_ROOT=~/Professional/Projects/InvenTree/dev/static' >> ~/.bashrc
echo 'export INVENTREE_BACKUP_DIR=~/Professional/Projects/InvenTree/dev/backup' >> ~/.bashrc
echo 'export INVENTREE_PLUGIN_DIR=~/Professional/Projects/InvenTree/dev/plugins' >> ~/.bashrc
echo 'export INVENTREE_CONFIG_FILE=~/Professional/Projects/InvenTree/dev/config.yaml' >> ~/.bashrc
echo 'export INVENTREE_SECRET_KEY_FILE=~/Professional/Projects/InvenTree/dev/secret_key.txt' >> ~/.bashrc
echo 'export INVENTREE_DEBUG=True' >> ~/.bashrc
echo 'export INVENTREE_PLUGINS_ENABLED=True' >> ~/.bashrc

# Reload shell
source ~/.bashrc
```

## What These Do

- `INVENTREE_DB_ENGINE=sqlite3` - Use SQLite for simplicity (you can switch to PostgreSQL later)
- `INVENTREE_STATIC_ROOT` - Where Django collects static files
- `INVENTREE_MEDIA_ROOT` - Where uploaded files are stored
- `INVENTREE_DEBUG=True` - Enable debug mode for development
- `INVENTREE_PLUGINS_ENABLED=True` - Enable plugins (required for AI procurement)

## After Server Starts

1. Open http://localhost:8000/admin
2. Log in with your superuser credentials
3. You should see "Ai Procurement" in the admin panel
4. Follow the testing guide to create test data

## Still Getting Errors?

If you still get errors about missing directories:

```bash
# Create required directories
mkdir -p dev/media dev/static dev/backup dev/plugins

# Try again
python manage.py migrate
```

## Next Steps

Once the server is running:
1. ✅ Access admin at http://localhost:8000/admin
2. ✅ Create test parts and suppliers
3. ✅ Test the AI procurement pipeline
4. ✅ Follow `TESTING_CHECKLIST.md`
