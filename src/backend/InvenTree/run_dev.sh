#!/bin/bash
# Development environment setup script

# Activate virtual environment
source venv/bin/activate

# Set required environment variables
export INVENTREE_DB_ENGINE=sqlite3
export INVENTREE_DB_NAME=../../../dev/database.sqlite3
export INVENTREE_STATIC_ROOT=../../../dev/static
export INVENTREE_MEDIA_ROOT=../../../dev/media
export INVENTREE_BACKUP_DIR=../../../dev/backup
export INVENTREE_CONFIG_FILE=../../../dev/config.yaml
export INVENTREE_SECRET_KEY_FILE=../../../dev/secret_key.txt
export INVENTREE_PLUGIN_FILE=../../../dev/plugins.txt
export INVENTREE_PLUGIN_DIR=../../../dev/plugins
export INVENTREE_DEBUG=True

# Run the command passed as arguments
"$@"
