# Migration Hanging Issue - Fix Summary

## Problem
Django migrations were hanging at "Skipping plugin loading sequence" because the AI Procurement app was trying to initialize database connections before the database was ready.

## Root Causes

1. **Module-level imports in signals.py**: The signals module imported `StateManager` and `compile_procurement_graph` at the top level, which triggered initialization during Django startup.

2. **Module-level imports in views.py**: The views module imported `StateManager` at the top level.

3. **Module-level imports in tasks.py**: The Celery tasks module imported both `StateManager` and `compile_procurement_graph` at the top level.

4. **Eager database connection in StateManager**: The `StateManager.__init__()` method immediately called `PostgresSaver.setup()`, which tried to connect to PostgreSQL during instantiation.

## Fixes Applied

### 1. signals.py
- **Removed**: Top-level imports of `StateManager` and `compile_procurement_graph`
- **Added**: Lazy imports inside `trigger_pipeline_async()` function
- **Result**: Signal handlers are registered during Django startup, but database connections are only made when signals are actually triggered

### 2. views.py
- **Removed**: Top-level import of `StateManager`
- **Added**: Lazy imports inside `PipelineStatusView.get()` and `ApprovalActionView.post()` methods
- **Result**: Views can be loaded during URL configuration without triggering database connections

### 3. tasks.py
- **Removed**: Top-level imports of `StateManager` and `compile_procurement_graph`
- **Added**: Lazy imports inside `run_pipeline_async()` task function
- **Result**: Celery tasks can be registered without triggering database connections

### 4. state_manager.py
- **Changed**: `StateManager.__init__()` no longer calls `PostgresSaver.setup()` immediately
- **Added**: `@property checkpointer` with lazy initialization
- **Added**: Database backend detection - uses PostgreSQL checkpointer for PostgreSQL, InMemorySaver for SQLite
- **Result**: StateManager can be imported without triggering database connections. The checkpointer is only initialized when first accessed. Works with both PostgreSQL and SQLite databases.

## Testing

To verify the fixes work:

```bash
# Activate virtual environment
cd ~/Professional/Projects/InvenTree/src/backend
source venv/bin/activate

# Set required environment variables
export INVENTREE_STATIC_ROOT="$(pwd)/InvenTree/static"
export INVENTREE_MEDIA_ROOT="$(pwd)/InvenTree/media"
export INVENTREE_BACKUP_DIR="$(pwd)/InvenTree/backup"
export INVENTREE_CONFIG_FILE="$(pwd)/InvenTree/config.yaml"

# Run migrations (should not hang)
cd InvenTree
python manage.py migrate
python manage.py makemigrations ai_procurement
python manage.py migrate ai_procurement
```

## Files Modified

1. `src/backend/InvenTree/ai_procurement/signals.py`
2. `src/backend/InvenTree/ai_procurement/views.py`
3. `src/backend/InvenTree/ai_procurement/tasks.py`
4. `src/backend/InvenTree/ai_procurement/state_manager.py`

## Key Principle

**Lazy Initialization**: Database connections and heavy initialization should be deferred until the first actual use, not during module import or class instantiation. This allows Django to:
- Load settings
- Register apps and models
- Run migrations
- Configure URLs

...all without triggering database operations that depend on tables that may not exist yet.

## Database Backend Support

The StateManager now automatically detects the database backend:

- **PostgreSQL**: Uses `PostgresSaver` for persistent state storage across restarts
- **SQLite**: Uses `InMemorySaver` for development (state is lost on restart)

For production deployments, PostgreSQL is recommended for full state persistence.
