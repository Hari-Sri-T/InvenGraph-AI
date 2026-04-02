# Migration from Celery to django-q2

## Issue
The AI Procurement system was originally designed to use Celery for background task processing, but InvenTree uses `django-q2` as its task queue system.

## Error
```
ModuleNotFoundError: No module named 'celery'
Location: /home/hari/Professional/Projects/InvenTree/src/backend/InvenTree/ai_procurement/tasks.py (Line 6)
```

## Solution
Migrated all background tasks from Celery to django-q2 to match InvenTree's architecture.

## Changes Made

### 1. tasks.py - Removed Celery Decorators
**File**: `src/backend/InvenTree/ai_procurement/tasks.py`

**Before**:
```python
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def run_pipeline_async(self, part_id: int, trigger_reason: str):
    # ... task code
    raise self.retry(exc=e, countdown=60 * (2**self.request.retries))
```

**After**:
```python
# No Celery imports needed

def run_pipeline_async(part_id: int, trigger_reason: str):
    # ... task code
    raise  # Let django-q2 handle retries
```

**Changes**:
- Removed `from celery import shared_task`
- Removed `@shared_task` decorators from all task functions
- Removed Celery-specific retry logic (django-q2 handles this)
- Removed `self` parameter from task functions

### 2. signals.py - Use InvenTree's offload_task
**File**: `src/backend/InvenTree/ai_procurement/signals.py`

**Before**:
```python
from .tasks import run_pipeline_async

# Queue the task using Celery
result = run_pipeline_async.delay(part_id, trigger_reason)
```

**After**:
```python
from InvenTree.tasks import offload_task

# Offload the task to django-q2
task_id = offload_task(
    'ai_procurement.tasks.run_pipeline_async',
    part_id,
    trigger_reason,
    force_async=False
)
```

**Changes**:
- Use InvenTree's `offload_task()` function instead of Celery's `.delay()`
- Task name is passed as a string path: `'ai_procurement.tasks.run_pipeline_async'`
- `force_async=False` allows fallback to synchronous execution if workers aren't running

### 3. requirements.txt - Removed Celery Dependency
**File**: `src/backend/InvenTree/ai_procurement/requirements.txt`

**Removed**:
```
celery>=5.3.0
```

**Added to comments**:
```
# Already included in InvenTree:
# - django-q2 (background task queue)
```

## django-q2 vs Celery

| Feature | Celery | django-q2 |
|---------|--------|-----------|
| **Broker** | Redis, RabbitMQ, etc. | Django ORM (database) |
| **Setup** | Separate broker required | No additional setup |
| **Workers** | `celery -A app worker` | `python manage.py qcluster` |
| **Task Definition** | `@shared_task` decorator | Plain Python functions |
| **Task Execution** | `task.delay()` or `task.apply_async()` | `offload_task()` or `async_task()` |
| **Retries** | Built-in with `retry()` | Configured in task call |
| **Monitoring** | Flower, Celery events | Django admin, django-q monitor |
| **Persistence** | Depends on broker | Django database |

## How django-q2 Works in InvenTree

### 1. Task Definition
Tasks are plain Python functions (no decorators needed):

```python
def my_background_task(arg1, arg2):
    # Do work
    return result
```

### 2. Task Execution
Use InvenTree's `offload_task()` helper:

```python
from InvenTree.tasks import offload_task

# Async execution (if workers running)
task_id = offload_task('app.module.my_background_task', arg1, arg2)

# Force async (fails if workers not running)
task_id = offload_task('app.module.my_background_task', arg1, arg2, force_async=True)

# Force sync (always runs immediately)
result = offload_task('app.module.my_background_task', arg1, arg2, force_sync=True)
```

### 3. Starting Workers
```bash
# Start django-q2 worker cluster
python manage.py qcluster
```

### 4. Monitoring Tasks
- Django Admin: `/admin/django_q/`
- View queued tasks: `OrmQ` model
- View completed tasks: `Success` model
- View failed tasks: `Failure` model

## Task Scheduling

For periodic tasks (like `check_expired_approvals`), use InvenTree's `schedule_task()`:

```python
from InvenTree.tasks import schedule_task

# Schedule task to run every hour
schedule_task(
    'ai_procurement.tasks.check_expired_approvals',
    schedule_type='H',  # Hourly
    repeats=-1  # Repeat indefinitely
)
```

This should be called in the app's `ready()` method:

```python
# ai_procurement/apps.py
class AIProcurementConfig(AppConfig):
    def ready(self):
        from InvenTree.tasks import schedule_task
        
        # Schedule periodic tasks
        schedule_task(
            'ai_procurement.tasks.check_expired_approvals',
            schedule_type='H',
            repeats=-1
        )
```

## Testing

### Without Workers (Synchronous)
Tasks will run synchronously if no workers are running:

```bash
# Just start the Django server
python manage.py runserver
```

Tasks triggered by signals will execute immediately in the same process.

### With Workers (Asynchronous)
Start workers in a separate terminal:

```bash
# Terminal 1: Start workers
python manage.py qcluster

# Terminal 2: Start Django server
python manage.py runserver
```

Tasks will be queued and executed by workers.

## Migration Checklist

- [x] Remove Celery imports from tasks.py
- [x] Remove `@shared_task` decorators
- [x] Update task function signatures (remove `self`)
- [x] Remove Celery-specific retry logic
- [x] Update signals.py to use `offload_task()`
- [x] Remove Celery from requirements.txt
- [x] Update documentation

## Benefits of django-q2

1. **Simpler Setup**: No separate broker (Redis/RabbitMQ) required
2. **Django Integration**: Uses Django ORM for persistence
3. **Easier Development**: Works without workers (falls back to sync)
4. **Built-in Monitoring**: Django admin interface
5. **Consistent with InvenTree**: Uses the same task system as the rest of the application

## Next Steps

1. Install dependencies:
   ```bash
   pip install -r src/backend/InvenTree/ai_procurement/requirements.txt
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

3. Start server (tasks will run synchronously):
   ```bash
   python manage.py runserver
   ```

4. (Optional) Start workers for async execution:
   ```bash
   python manage.py qcluster
   ```

## References

- [django-q2 Documentation](https://django-q2.readthedocs.io/)
- [InvenTree Tasks Documentation](https://docs.inventree.org/)
- InvenTree's task implementation: `src/backend/InvenTree/InvenTree/tasks.py`
