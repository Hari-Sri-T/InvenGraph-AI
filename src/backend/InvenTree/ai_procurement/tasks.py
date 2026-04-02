"""Background tasks for asynchronous pipeline execution using django-q2."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def run_pipeline_async(part_id: int, trigger_reason: str) -> Optional[str]:
    """
    Execute procurement pipeline asynchronously.

    This task runs the LangGraph pipeline until it reaches the human approval
    interrupt point. The pipeline will be persisted and can be resumed after
    approval.

    Args:
        part_id: ID of the part to process
        trigger_reason: Reason for triggering the pipeline

    Returns:
        Pipeline ID if successful, None otherwise
    """
    try:
        logger.info(
            f'Starting async pipeline execution for part {part_id}: {trigger_reason}'
        )

        # Lazy imports to avoid database access during migration
        from .graph import compile_procurement_graph
        from .state_manager import StateManager

        # Initialize state manager and graph
        state_manager = StateManager()
        graph = compile_procurement_graph()

        # Initialize pipeline
        pipeline_id, initial_state = state_manager.initialize_pipeline(
            part_id, trigger_reason
        )

        # Execute graph until interrupt (human approval)
        config = {'configurable': {'thread_id': pipeline_id}}

        try:
            result = graph.invoke(initial_state, config)
            logger.info(
                f'Pipeline {pipeline_id} executed successfully, '
                f'waiting for human approval'
            )
            return pipeline_id
        except Exception as graph_error:
            logger.error(
                f'Error executing graph for pipeline {pipeline_id}: {graph_error}',
                exc_info=True,
            )
            # Mark pipeline as failed
            state_manager.mark_pipeline_failed(pipeline_id, str(graph_error))
            raise

    except Exception as e:
        logger.error(
            f'Error in async pipeline task for part {part_id}: {e}', exc_info=True
        )
        raise


def retrain_prophet_model_async(part_id: int) -> bool:
    """
    Retrain Prophet model asynchronously.

    Args:
        part_id: ID of the part

    Returns:
        True if successful, False otherwise
    """
    try:
        from .learning.learning_layer import LearningLayer

        logger.info(f'Starting Prophet model retraining for part {part_id}')

        learning_layer = LearningLayer()
        learning_layer.retrain_prophet_model(part_id)

        logger.info(f'Prophet model retraining completed for part {part_id}')
        return True
    except Exception as e:
        logger.error(
            f'Error retraining Prophet model for part {part_id}: {e}', exc_info=True
        )
        return False


def update_learning_metrics_async(pipeline_id: str) -> bool:
    """
    Update learning metrics asynchronously after pipeline completion.

    This includes:
    - EMA trend calculation
    - Reorder point adjustment
    - Supplier reliability scoring

    Args:
        pipeline_id: ID of the completed pipeline

    Returns:
        True if successful, False otherwise
    """
    try:
        from .learning.learning_layer import LearningLayer
        from .models import PipelineExecution

        logger.info(f'Starting learning metrics update for pipeline {pipeline_id}')

        # Get pipeline execution
        pipeline = PipelineExecution.objects.get(pipeline_id=pipeline_id)
        part_id = pipeline.part_id

        learning_layer = LearningLayer()

        # Update EMA trends
        learning_layer.update_ema_trends(part_id)

        # Adjust reorder point
        learning_layer.adjust_reorder_point(part_id)

        # Update supplier reliability (if supplier was used)
        if pipeline.state_data.get('supplier_id'):
            learning_layer.update_supplier_reliability(
                pipeline.state_data['supplier_id'], part_id
            )

        logger.info(f'Learning metrics update completed for pipeline {pipeline_id}')
        return True
    except Exception as e:
        logger.error(
            f'Error updating learning metrics for pipeline {pipeline_id}: {e}',
            exc_info=True,
        )
        return False


def send_email_notification_async(
    recipient_emails: list[str], subject: str, message: str, html_message: str = None
) -> bool:
    """
    Send email notification asynchronously.

    Args:
        recipient_emails: List of recipient email addresses
        subject: Email subject
        message: Plain text message
        html_message: HTML message (optional)

    Returns:
        True if successful, False otherwise
    """
    try:
        from django.core.mail import send_mail

        logger.info(f'Sending email notification to {len(recipient_emails)} recipients')

        send_mail(
            subject=subject,
            message=message,
            from_email=None,  # Use default from settings
            recipient_list=recipient_emails,
            html_message=html_message,
            fail_silently=False,
        )

        logger.info('Email notification sent successfully')
        return True
    except Exception as e:
        logger.error(f'Error sending email notification: {e}', exc_info=True)
        return False


def check_expired_approvals() -> int:
    """
    Periodic task to check for expired approval requests.

    Marks expired requests as "expired" and rejects the pipeline.

    Returns:
        Number of expired approvals processed
    """
    try:
        from datetime import datetime

        from .models import ApprovalRequest

        logger.info('Checking for expired approval requests')

        # Find expired approvals
        now = datetime.now()
        expired_approvals = ApprovalRequest.objects.filter(
            status='pending', expires_at__lt=now
        )

        count = 0
        for approval in expired_approvals:
            try:
                # Mark as expired
                approval.status = 'expired'
                approval.save()

                # Mark pipeline as rejected
                from .state_manager import StateManager

                state_manager = StateManager()
                state_manager.mark_pipeline_rejected(
                    approval.pipeline_execution.pipeline_id, 'Approval request expired'
                )

                count += 1
                logger.info(
                    f'Marked approval request {approval.id} as expired '
                    f'for pipeline {approval.pipeline_execution.pipeline_id}'
                )
            except Exception as e:
                logger.error(
                    f'Error processing expired approval {approval.id}: {e}',
                    exc_info=True,
                )

        logger.info(f'Processed {count} expired approval requests')
        return count
    except Exception as e:
        logger.error(f'Error checking expired approvals: {e}', exc_info=True)
        return 0
