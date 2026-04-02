"""Django signal handlers for event-driven pipeline triggering."""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from django.core.cache import cache
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from part.models import Part
from stock.models import StockItem


class EventDeduplicator:
    """Handles event deduplication to prevent duplicate pipeline triggers."""

    DEDUPLICATION_WINDOW_SECONDS = 60

    @staticmethod
    def should_trigger(part_id: int) -> bool:
        """
        Check if pipeline should be triggered for this part.

        Args:
            part_id: ID of the part

        Returns:
            True if pipeline should trigger, False if deduplicated
        """
        cache_key = f'ai_procurement_event_{part_id}'
        last_trigger = cache.get(cache_key)

        if last_trigger:
            # Event already triggered recently, deduplicate
            return False

        # Mark event as triggered
        cache.set(
            cache_key,
            datetime.now().isoformat(),
            EventDeduplicator.DEDUPLICATION_WINDOW_SECONDS,
        )
        return True


def calculate_total_stock(part: Part) -> float:
    """
    Calculate total stock for a part across all locations.

    Args:
        part: Part instance

    Returns:
        Total stock quantity
    """
    stock_items = StockItem.objects.filter(part=part)
    total = stock_items.aggregate(total=Sum('quantity'))['total']
    return float(total or 0)


def should_trigger_pipeline(part: Part, current_stock: float) -> tuple[bool, str]:
    """
    Determine if pipeline should be triggered based on stock level.

    Args:
        part: Part instance
        current_stock: Current total stock level

    Returns:
        Tuple of (should_trigger, trigger_reason)
    """
    reorder_point = float(part.minimum_stock or 0)

    if reorder_point <= 0:
        # No reorder point set, don't trigger
        return False, ''

    if current_stock < reorder_point:
        trigger_reason = (
            f'Stock level ({current_stock}) below reorder point ({reorder_point})'
        )
        return True, trigger_reason

    return False, ''


def trigger_pipeline_async(part_id: int, trigger_reason: str) -> Optional[str]:
    """
    Trigger procurement pipeline asynchronously.

    Args:
        part_id: ID of the part
        trigger_reason: Reason for triggering

    Returns:
        Pipeline ID if successful, None otherwise
    """
    try:
        # Try to use InvenTree's task queue (django-q2)
        try:
            from InvenTree.tasks import offload_task

            # Offload the task to django-q2
            task_id = offload_task(
                'ai_procurement.tasks.run_pipeline_async',
                part_id,
                trigger_reason,
                force_async=False  # Will run sync if workers not available
            )
            
            if task_id:
                print(f'Queued async pipeline task {task_id} for part {part_id}')
                # Note: task_id is the django-q task ID, not the pipeline ID
                # The actual pipeline ID will be returned by the task
                return str(task_id)
            else:
                # Task ran synchronously, return success
                print(f'Pipeline task ran synchronously for part {part_id}')
                return None
                
        except (ImportError, Exception) as e:
            # Task queue not available, run synchronously
            print(f'Task queue not available ({e}), running pipeline synchronously')

            # Lazy imports to avoid circular dependencies and database access during migration
            from .graph import compile_procurement_graph
            from .state_manager import StateManager

            # Initialize state manager and graph
            state_manager = StateManager()
            graph = compile_procurement_graph()

            # Initialize pipeline
            pipeline_id, initial_state = state_manager.initialize_pipeline(
                part_id, trigger_reason
            )

            # Execute graph synchronously
            config = {'configurable': {'thread_id': pipeline_id}}

            # Run graph until interrupt (human approval)
            result = graph.invoke(initial_state, config)

            return pipeline_id
    except Exception as e:
        print(f'Error triggering pipeline: {e}')
        return None


@receiver(post_save, sender=StockItem)
def on_stock_item_change(sender, instance, created, **kwargs):
    """
    Signal handler for StockItem changes.

    Triggers procurement pipeline when stock falls below reorder point.

    Args:
        sender: Model class (StockItem)
        instance: StockItem instance that was saved
        created: True if new instance was created
        **kwargs: Additional keyword arguments
    """
    try:
        part = instance.part

        # Check deduplication
        if not EventDeduplicator.should_trigger(part.id):
            return

        # Calculate total stock
        current_stock = calculate_total_stock(part)

        # Check if pipeline should trigger
        should_trigger, trigger_reason = should_trigger_pipeline(part, current_stock)

        if should_trigger:
            print(
                f'Triggering procurement pipeline for part {part.id}: {trigger_reason}'
            )
            pipeline_id = trigger_pipeline_async(part.id, trigger_reason)
            if pipeline_id:
                print(f'Pipeline {pipeline_id} started for part {part.id}')
            else:
                print(f'Failed to start pipeline for part {part.id}')
    except Exception as e:
        print(f'Error in stock change signal handler: {e}')


def calculate_projected_stock(part: Part, additional_demand: float) -> float:
    """
    Calculate projected stock after fulfilling additional demand.

    Args:
        part: Part instance
        additional_demand: Additional demand quantity

    Returns:
        Projected stock level
    """
    current_stock = calculate_total_stock(part)
    return current_stock - additional_demand


@receiver(post_save, sender='order.SalesOrderLineItem')
def on_sales_order_line_item_change(sender, instance, created, **kwargs):
    """
    Signal handler for SalesOrderLineItem changes.

    Triggers procurement pipeline when projected stock will fall below reorder point.

    Args:
        sender: Model class (SalesOrderLineItem)
        instance: SalesOrderLineItem instance that was saved
        created: True if new instance was created
        **kwargs: Additional keyword arguments
    """
    # Only trigger on new sales orders
    if not created:
        return

    try:
        part = instance.part

        # Check deduplication
        if not EventDeduplicator.should_trigger(part.id):
            return

        # Calculate projected stock after order fulfillment
        projected_stock = calculate_projected_stock(part, float(instance.quantity))

        # Check if pipeline should trigger based on projected stock
        reorder_point = float(part.minimum_stock or 0)

        if reorder_point <= 0:
            return

        if projected_stock < reorder_point:
            trigger_reason = (
                f'Projected stock ({projected_stock}) after sales order '
                f'will fall below reorder point ({reorder_point})'
            )
            print(
                f'Triggering procurement pipeline for part {part.id}: {trigger_reason}'
            )
            pipeline_id = trigger_pipeline_async(part.id, trigger_reason)
            if pipeline_id:
                print(f'Pipeline {pipeline_id} started for part {part.id}')
            else:
                print(f'Failed to start pipeline for part {part.id}')
    except Exception as e:
        print(f'Error in sales order line item signal handler: {e}')
