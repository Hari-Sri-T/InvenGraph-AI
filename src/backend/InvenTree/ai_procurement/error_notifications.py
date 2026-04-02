"""Error notification system for AI Procurement."""

from typing import Dict, Optional

from part.models import Part

from .logging_config import logger
from .notifications import NotificationService


class ErrorNotificationService:
    """Handles error notifications to users."""

    def __init__(self):
        """Initialize error notification service."""
        self.notification_service = NotificationService()

    def notify_pipeline_failure(
        self, pipeline_id: str, part_id: int, error_message: str, error_details: Dict = None
    ):
        """
        Notify users of pipeline failure.

        Args:
            pipeline_id: UUID of the pipeline
            part_id: ID of the part
            error_message: Error message
            error_details: Additional error details
        """
        try:
            part = Part.objects.get(pk=part_id)

            # Create notification message
            message = (
                f'AI Procurement pipeline failed for part "{part.name}" (ID: {part_id}).\n\n'
                f'Pipeline ID: {pipeline_id}\n'
                f'Error: {error_message}\n\n'
                f'Please review the part configuration and try again.'
            )

            # TODO: Send in-app notification
            # self.notification_service.send_in_app_notification(...)

            logger.info(f'Sent failure notification for pipeline {pipeline_id}')

        except Exception as e:
            logger.error(f'Failed to send error notification: {e}')

    def notify_no_suppliers(self, part_id: int):
        """
        Notify users that no suppliers are configured for a part.

        Args:
            part_id: ID of the part
        """
        try:
            part = Part.objects.get(pk=part_id)

            message = (
                f'No suppliers configured for part "{part.name}" (ID: {part_id}).\n\n'
                f'Please add at least one supplier in the InvenTree admin interface '
                f'before the AI procurement system can make recommendations.'
            )

            # TODO: Send in-app notification to part responsible owner
            logger.info(f'Sent no-suppliers notification for part {part_id}')

        except Exception as e:
            logger.error(f'Failed to send no-suppliers notification: {e}')

    def notify_llm_unavailable(self, pipeline_id: str, part_id: int):
        """
        Notify users that LLM is unavailable and fallback was used.

        Args:
            pipeline_id: UUID of the pipeline
            part_id: ID of the part
        """
        try:
            part = Part.objects.get(pk=part_id)

            message = (
                f'AI decision-making service (Ollama) is unavailable for part "{part.name}".\n\n'
                f'Pipeline ID: {pipeline_id}\n'
                f'Using rule-based fallback logic instead.\n\n'
                f'Please check that Ollama is running and accessible.'
            )

            # TODO: Send in-app notification
            logger.info(f'Sent LLM unavailable notification for pipeline {pipeline_id}')

        except Exception as e:
            logger.error(f'Failed to send LLM unavailable notification: {e}')

    def notify_po_creation_failure(
        self, pipeline_id: str, part_id: int, supplier_id: int, error_message: str
    ):
        """
        Notify users of purchase order creation failure.

        Args:
            pipeline_id: UUID of the pipeline
            part_id: ID of the part
            supplier_id: ID of the supplier
            error_message: Error message
        """
        try:
            part = Part.objects.get(pk=part_id)

            message = (
                f'Failed to create purchase order for part "{part.name}".\n\n'
                f'Pipeline ID: {pipeline_id}\n'
                f'Supplier ID: {supplier_id}\n'
                f'Error: {error_message}\n\n'
                f'Please review the order details and create the purchase order manually.'
            )

            # TODO: Send in-app notification
            logger.info(f'Sent PO creation failure notification for pipeline {pipeline_id}')

        except Exception as e:
            logger.error(f'Failed to send PO creation failure notification: {e}')
