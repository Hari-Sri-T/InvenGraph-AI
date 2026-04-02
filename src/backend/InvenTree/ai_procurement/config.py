"""Configuration parameters for Agentic AI Procurement System."""

import os
from typing import Dict


class ProcurementConfig:
    """Configuration for AI procurement system."""

    # Supplier Ranking Weights
    PRICE_WEIGHT = float(os.getenv('AI_PROCUREMENT_PRICE_WEIGHT', '0.4'))
    LEAD_TIME_WEIGHT = float(os.getenv('AI_PROCUREMENT_LEAD_TIME_WEIGHT', '0.3'))
    RELIABILITY_WEIGHT = float(os.getenv('AI_PROCUREMENT_RELIABILITY_WEIGHT', '0.3'))

    # Demand Forecasting
    FORECAST_HORIZON_DAYS = int(os.getenv('AI_PROCUREMENT_FORECAST_DAYS', '30'))
    LOOKBACK_DAYS = int(os.getenv('AI_PROCUREMENT_LOOKBACK_DAYS', '180'))
    MIN_DATA_POINTS = int(os.getenv('AI_PROCUREMENT_MIN_DATA_POINTS', '14'))

    # Prophet Model Caching
    PROPHET_CACHE_TTL_DAYS = int(os.getenv('AI_PROCUREMENT_PROPHET_CACHE_TTL', '7'))

    # Approval Settings
    APPROVAL_TIMEOUT_DAYS = int(os.getenv('AI_PROCUREMENT_APPROVAL_TIMEOUT', '7'))

    # Learning Layer
    EMA_ALPHA = float(os.getenv('AI_PROCUREMENT_EMA_ALPHA', '0.3'))
    CALCULATION_PERIOD_DAYS = int(
        os.getenv('AI_PROCUREMENT_CALCULATION_PERIOD', '90')
    )

    # Ollama Settings
    OLLAMA_URL = os.getenv(
        'AI_PROCUREMENT_OLLAMA_URL', 'http://host.docker.internal:11434/api/generate'
    )
    OLLAMA_MODEL = os.getenv('AI_PROCUREMENT_OLLAMA_MODEL', 'llama3')
    OLLAMA_TIMEOUT = int(os.getenv('AI_PROCUREMENT_OLLAMA_TIMEOUT', '45'))
    OLLAMA_TEMPERATURE = float(os.getenv('AI_PROCUREMENT_OLLAMA_TEMPERATURE', '0.3'))

    # Event Deduplication
    DEDUPLICATION_WINDOW_SECONDS = int(
        os.getenv('AI_PROCUREMENT_DEDUPLICATION_WINDOW', '60')
    )

    # Reorder Point Adjustment
    REORDER_INCREASE_FACTOR = float(
        os.getenv('AI_PROCUREMENT_REORDER_INCREASE_FACTOR', '1.2')
    )
    REORDER_DECREASE_FACTOR = float(
        os.getenv('AI_PROCUREMENT_REORDER_DECREASE_FACTOR', '0.9')
    )
    REORDER_MAX_MULTIPLIER = float(
        os.getenv('AI_PROCUREMENT_REORDER_MAX_MULTIPLIER', '10.0')
    )

    # Forecast Accuracy Thresholds
    LOW_ACCURACY_THRESHOLD = float(
        os.getenv('AI_PROCUREMENT_LOW_ACCURACY_THRESHOLD', '0.7')
    )
    HIGH_ACCURACY_THRESHOLD = float(
        os.getenv('AI_PROCUREMENT_HIGH_ACCURACY_THRESHOLD', '0.9')
    )
    STOCKOUT_THRESHOLD = int(os.getenv('AI_PROCUREMENT_STOCKOUT_THRESHOLD', '2'))

    @classmethod
    def validate_config(cls) -> tuple[bool, str]:
        """
        Validate configuration parameters.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate weights sum to 1.0
        weights_sum = cls.PRICE_WEIGHT + cls.LEAD_TIME_WEIGHT + cls.RELIABILITY_WEIGHT
        if abs(weights_sum - 1.0) > 0.01:
            return False, f'Supplier ranking weights must sum to 1.0, got {weights_sum}'

        # Validate positive values
        if cls.FORECAST_HORIZON_DAYS <= 0:
            return False, 'Forecast horizon must be positive'

        if cls.APPROVAL_TIMEOUT_DAYS <= 0:
            return False, 'Approval timeout must be positive'

        if not (0 < cls.EMA_ALPHA < 1):
            return False, 'EMA alpha must be between 0 and 1'

        if cls.PROPHET_CACHE_TTL_DAYS <= 0:
            return False, 'Prophet cache TTL must be positive'

        return True, ''

    @classmethod
    def get_config_dict(cls) -> Dict:
        """
        Get all configuration as dictionary.

        Returns:
            Dictionary with all configuration parameters
        """
        return {
            'supplier_ranking': {
                'price_weight': cls.PRICE_WEIGHT,
                'lead_time_weight': cls.LEAD_TIME_WEIGHT,
                'reliability_weight': cls.RELIABILITY_WEIGHT,
            },
            'demand_forecasting': {
                'forecast_horizon_days': cls.FORECAST_HORIZON_DAYS,
                'lookback_days': cls.LOOKBACK_DAYS,
                'min_data_points': cls.MIN_DATA_POINTS,
                'prophet_cache_ttl_days': cls.PROPHET_CACHE_TTL_DAYS,
            },
            'approval': {'timeout_days': cls.APPROVAL_TIMEOUT_DAYS},
            'learning': {
                'ema_alpha': cls.EMA_ALPHA,
                'calculation_period_days': cls.CALCULATION_PERIOD_DAYS,
            },
            'ollama': {
                'url': cls.OLLAMA_URL,
                'model': cls.OLLAMA_MODEL,
                'timeout': cls.OLLAMA_TIMEOUT,
                'temperature': cls.OLLAMA_TEMPERATURE,
            },
            'event_handling': {
                'deduplication_window_seconds': cls.DEDUPLICATION_WINDOW_SECONDS
            },
            'reorder_adjustment': {
                'increase_factor': cls.REORDER_INCREASE_FACTOR,
                'decrease_factor': cls.REORDER_DECREASE_FACTOR,
                'max_multiplier': cls.REORDER_MAX_MULTIPLIER,
            },
            'thresholds': {
                'low_accuracy_threshold': cls.LOW_ACCURACY_THRESHOLD,
                'high_accuracy_threshold': cls.HIGH_ACCURACY_THRESHOLD,
                'stockout_threshold': cls.STOCKOUT_THRESHOLD,
            },
        }


# Validate configuration on import
is_valid, error_message = ProcurementConfig.validate_config()
if not is_valid:
    print(f'WARNING: Invalid AI Procurement configuration: {error_message}')
