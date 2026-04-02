"""Centralized logging configuration for AI Procurement."""

import logging
import sys
from typing import Any, Dict

# Configure logger
logger = logging.getLogger('ai_procurement')
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
console_handler.setFormatter(formatter)

# Add handler to logger
if not logger.handlers:
    logger.addHandler(console_handler)


def log_pipeline_transition(
    pipeline_id: str, part_id: int, from_node: str, to_node: str, duration_ms: int = 0
):
    """
    Log pipeline node transition.

    Args:
        pipeline_id: UUID of the pipeline
        part_id: ID of the part
        from_node: Source node name
        to_node: Destination node name
        duration_ms: Duration in milliseconds
    """
    logger.info(
        f'Pipeline {pipeline_id} | Part {part_id} | '
        f'Transition: {from_node} → {to_node} | '
        f'Duration: {duration_ms}ms'
    )


def log_agent_output(
    pipeline_id: str, part_id: int, agent_name: str, output_summary: Dict[str, Any]
):
    """
    Log agent output.

    Args:
        pipeline_id: UUID of the pipeline
        part_id: ID of the part
        agent_name: Name of the agent
        output_summary: Summary of agent output (no sensitive data)
    """
    logger.info(
        f'Pipeline {pipeline_id} | Part {part_id} | '
        f'Agent: {agent_name} | '
        f'Output: {output_summary}'
    )


def log_error(
    pipeline_id: str,
    part_id: int,
    component: str,
    error_message: str,
    error_details: Dict[str, Any] = None,
):
    """
    Log error with context.

    Args:
        pipeline_id: UUID of the pipeline
        part_id: ID of the part
        component: Component where error occurred
        error_message: Error message
        error_details: Additional error details (no sensitive data)
    """
    logger.error(
        f'Pipeline {pipeline_id} | Part {part_id} | '
        f'Component: {component} | '
        f'Error: {error_message} | '
        f'Details: {error_details or {}}'
    )


def log_performance_metric(
    pipeline_id: str, part_id: int, metric_name: str, metric_value: float, unit: str
):
    """
    Log performance metric.

    Args:
        pipeline_id: UUID of the pipeline
        part_id: ID of the part
        metric_name: Name of the metric
        metric_value: Metric value
        unit: Unit of measurement
    """
    logger.info(
        f'Pipeline {pipeline_id} | Part {part_id} | '
        f'Metric: {metric_name} = {metric_value} {unit}'
    )


def sanitize_for_logging(data: Any) -> Any:
    """
    Sanitize data for logging (remove sensitive information).

    Args:
        data: Data to sanitize

    Returns:
        Sanitized data
    """
    if isinstance(data, dict):
        sanitized = {}
        sensitive_keys = ['password', 'api_key', 'token', 'secret', 'credential']

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'
            else:
                sanitized[key] = sanitize_for_logging(value)

        return sanitized
    elif isinstance(data, list):
        return [sanitize_for_logging(item) for item in data]
    else:
        return data
