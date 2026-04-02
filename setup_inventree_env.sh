#!/bin/bash
# Quick setup script for InvenTree environment

# Set required environment variables
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

# AI Procurement specific settings
export AI_PROCUREMENT_OLLAMA_URL=http://localhost:11434/api/generate
export AI_PROCUREMENT_PRICE_WEIGHT=0.4
export AI_PROCUREMENT_LEAD_TIME_WEIGHT=0.3
export AI_PROCUREMENT_RELIABILITY_WEIGHT=0.3
export AI_PROCUREMENT_FORECAST_DAYS=30
export AI_PROCUREMENT_APPROVAL_TIMEOUT_DAYS=7
export AI_PROCUREMENT_EMA_ALPHA=0.3
export AI_PROCUREMENT_PROPHET_CACHE_TTL_DAYS=7

echo "✓ Environment variables set"
echo ""
echo "Now you can run:"
echo "  python manage.py migrate"
echo "  python manage.py makemigrations ai_procurement"
echo "  python manage.py migrate ai_procurement"
echo "  python manage.py createsuperuser"
echo "  python manage.py runserver 0.0.0.0:8000"
