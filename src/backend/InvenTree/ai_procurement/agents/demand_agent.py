"""Demand Agent: Forecasts future demand using Prophet with XGBoost fallback."""

import hashlib
import pickle
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

import pandas as pd
from django.db.models import Sum
from prophet import Prophet

from build.models import Build
from order.models import SalesOrderLineItem
from part.models import Part
from stock.models import StockItemTracking

from ..logging_config import log_agent_output, log_error, logger
from ..models import DemandForecast, ProphetModelCache


class DemandAgent:
    """Agent responsible for demand forecasting using Prophet."""

    LOOKBACK_DAYS = 180
    PROPHET_CACHE_TTL_DAYS = 7
    MIN_DATA_POINTS = 14

    def __init__(self):
        """Initialize Demand Agent."""
        pass

    def get_historical_consumption(
        self, part_id: int, lookback_days: int = LOOKBACK_DAYS
    ) -> pd.DataFrame:
        """
        Gather historical consumption data for a part.

        Args:
            part_id: ID of the part
            lookback_days: Number of days to look back

        Returns:
            DataFrame with columns [ds: date, y: consumption]
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=lookback_days)

        # Initialize date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        consumption_df = pd.DataFrame({'ds': date_range, 'y': 0.0})

        try:
            part = Part.objects.get(pk=part_id)

            # Aggregate consumption from multiple sources
            # 1. Stock movements (negative quantities = consumption)
            stock_movements = StockItemTracking.objects.filter(
                item__part=part,
                date__gte=start_date,
                date__lte=end_date,
                quantity__lt=0,  # Negative = consumption
            ).values('date').annotate(total=Sum('quantity'))

            for movement in stock_movements:
                date = movement['date'].date() if hasattr(movement['date'], 'date') else movement['date']
                consumption = abs(float(movement['total']))
                consumption_df.loc[consumption_df['ds'] == pd.Timestamp(date), 'y'] += consumption

            # 2. Sales order line items (allocated/shipped)
            sales_lines = SalesOrderLineItem.objects.filter(
                part=part,
                order__shipment_date__gte=start_date,
                order__shipment_date__lte=end_date,
            ).values('order__shipment_date').annotate(total=Sum('quantity'))

            for sale in sales_lines:
                if sale['order__shipment_date']:
                    date = sale['order__shipment_date']
                    consumption = float(sale['total'])
                    consumption_df.loc[consumption_df['ds'] == pd.Timestamp(date), 'y'] += consumption

            # 3. Build orders (parts consumed in production)
            builds = Build.objects.filter(
                part=part,
                completion_date__gte=start_date,
                completion_date__lte=end_date,
            ).values('completion_date').annotate(total=Sum('quantity'))

            for build in builds:
                if build['completion_date']:
                    date = build['completion_date']
                    consumption = float(build['total'])
                    consumption_df.loc[consumption_df['ds'] == pd.Timestamp(date), 'y'] += consumption

        except Part.DoesNotExist:
            pass
        except Exception as e:
            print(f'Error gathering historical consumption: {e}')

        return consumption_df

    def get_cached_prophet_model(self, part_id: int) -> Optional[Prophet]:
        """
        Retrieve cached Prophet model if available and fresh.

        Args:
            part_id: ID of the part

        Returns:
            Prophet model if cached and fresh, None otherwise
        """
        try:
            cache_entry = ProphetModelCache.objects.get(part_id=part_id)

            # Check if model is fresh (within TTL)
            age_days = (datetime.now() - cache_entry.training_date).days
            if age_days > self.PROPHET_CACHE_TTL_DAYS:
                return None

            # Deserialize model
            model = pickle.loads(cache_entry.model_binary)
            return model
        except ProphetModelCache.DoesNotExist:
            return None
        except Exception as e:
            print(f'Error loading cached model: {e}')
            return None

    def cache_prophet_model(
        self, part_id: int, model: Prophet, training_data: pd.DataFrame
    ):
        """
        Cache trained Prophet model for future use.

        Args:
            part_id: ID of the part
            model: Trained Prophet model
            training_data: DataFrame used for training
        """
        try:
            # Serialize model
            model_binary = pickle.dumps(model)

            # Calculate data hash
            data_hash = hashlib.sha256(training_data.to_json().encode()).hexdigest()

            # Update or create cache entry
            ProphetModelCache.objects.update_or_create(
                part_id=part_id,
                defaults={
                    'model_binary': model_binary,
                    'training_data_hash': data_hash,
                    'training_samples_count': len(training_data),
                    'model_performance_metrics': {},
                    'version': 1,
                },
            )
        except Exception as e:
            print(f'Error caching model: {e}')

    def train_prophet_model(self, historical_data: pd.DataFrame) -> Prophet:
        """
        Train Prophet model on historical data.

        Args:
            historical_data: DataFrame with columns [ds, y]

        Returns:
            Trained Prophet model
        """
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=False,
            changepoint_prior_scale=0.05,
        )

        # Suppress verbose output
        import logging
        logging.getLogger('prophet').setLevel(logging.WARNING)

        model.fit(historical_data)
        return model

    def detect_seasonality(self, forecast_df: pd.DataFrame) -> bool:
        """
        Detect if seasonality is present in forecast.

        Args:
            forecast_df: Prophet forecast DataFrame

        Returns:
            True if seasonality detected, False otherwise
        """
        # Check if weekly or daily seasonality components exist
        if 'weekly' in forecast_df.columns or 'daily' in forecast_df.columns:
            return True
        return False

    def analyze_trend(self, trend_series: pd.Series) -> str:
        """
        Analyze trend direction from Prophet forecast.

        Args:
            trend_series: Trend component from Prophet

        Returns:
            Trend direction: 'increasing', 'decreasing', or 'stable'
        """
        if len(trend_series) < 2:
            return 'unknown'

        # Compare first and last values
        start_value = trend_series.iloc[0]
        end_value = trend_series.iloc[-1]
        change_pct = (end_value - start_value) / start_value if start_value != 0 else 0

        if change_pct > 0.1:
            return 'increasing'
        elif change_pct < -0.1:
            return 'decreasing'
        else:
            return 'stable'

    def forecast_demand(
        self, part_id: int, forecast_days: int = 30
    ) -> Dict:
        """
        Forecast demand for a part using Prophet.

        Args:
            part_id: ID of the part
            forecast_days: Number of days to forecast

        Returns:
            Dictionary with forecast results
        """
        try:
            # Get historical data
            historical_data = self.get_historical_consumption(part_id, self.LOOKBACK_DAYS)

            # Check if sufficient data
            non_zero_days = (historical_data['y'] > 0).sum()
            if non_zero_days < self.MIN_DATA_POINTS:
                logger.warning(
                    f'Insufficient data for Prophet (part {part_id}): '
                    f'{non_zero_days} non-zero days, need {self.MIN_DATA_POINTS}. '
                    f'Using simple moving average fallback.'
                )
                # Insufficient data, use simple moving average
                avg_daily_consumption = historical_data['y'].mean()
                predicted_demand = avg_daily_consumption * forecast_days

                return {
                    'part_id': part_id,
                    'forecast_horizon_days': forecast_days,
                    'predicted_demand': max(0, float(predicted_demand)),
                    'confidence_lower': max(0, float(predicted_demand * 0.8)),
                    'confidence_upper': max(0, float(predicted_demand * 1.2)),
                    'model_used': 'simple_average',
                    'seasonality_detected': False,
                    'trend_direction': 'unknown',
                    'forecast_accuracy_score': None,
                }

            try:
                # Check for cached model
                model = self.get_cached_prophet_model(part_id)

                if model is None:
                    logger.info(f'Training new Prophet model for part {part_id}')
                    # Train new model
                    model = self.train_prophet_model(historical_data)
                    # Cache the model
                    self.cache_prophet_model(part_id, model, historical_data)
                else:
                    logger.info(f'Using cached Prophet model for part {part_id}')

                # Generate forecast
                future_df = model.make_future_dataframe(periods=forecast_days, freq='D')
                forecast_df = model.predict(future_df)

                # Extract future predictions
                future_forecast = forecast_df.tail(forecast_days)
                predicted_demand = future_forecast['yhat'].sum()
                confidence_lower = future_forecast['yhat_lower'].sum()
                confidence_upper = future_forecast['yhat_upper'].sum()

                # Detect seasonality and trend
                seasonality_detected = self.detect_seasonality(forecast_df)
                trend_direction = self.analyze_trend(forecast_df['trend'])

                # Ensure non-negative values
                predicted_demand = max(0, float(predicted_demand))
                confidence_lower = max(0, float(confidence_lower))
                confidence_upper = max(0, float(confidence_upper))

                logger.info(
                    f'Prophet forecast for part {part_id}: '
                    f'demand={predicted_demand:.2f}, '
                    f'trend={trend_direction}, '
                    f'seasonality={seasonality_detected}'
                )

                return {
                    'part_id': part_id,
                    'forecast_horizon_days': forecast_days,
                    'predicted_demand': predicted_demand,
                    'confidence_lower': confidence_lower,
                    'confidence_upper': confidence_upper,
                    'model_used': 'prophet',
                    'seasonality_detected': seasonality_detected,
                    'trend_direction': trend_direction,
                    'forecast_accuracy_score': None,  # Calculated later
                }

            except Exception as prophet_error:
                logger.error(
                    f'Prophet forecasting failed for part {part_id}: {prophet_error}. '
                    f'Falling back to simple average.'
                )
                # Fallback to simple average
                avg_daily_consumption = historical_data['y'].mean()
                predicted_demand = avg_daily_consumption * forecast_days

                return {
                    'part_id': part_id,
                    'forecast_horizon_days': forecast_days,
                    'predicted_demand': max(0, float(predicted_demand)),
                    'confidence_lower': max(0, float(predicted_demand * 0.8)),
                    'confidence_upper': max(0, float(predicted_demand * 1.2)),
                    'model_used': 'simple_average',
                    'seasonality_detected': False,
                    'trend_direction': 'unknown',
                    'forecast_accuracy_score': None,
                }

        except Exception as e:
            log_error(
                pipeline_id='unknown',
                part_id=part_id,
                component='DemandAgent',
                error_message=f'Forecast demand failed: {str(e)}',
                error_details={'forecast_days': forecast_days},
            )
            # Return zero forecast as last resort
            return {
                'part_id': part_id,
                'forecast_horizon_days': forecast_days,
                'predicted_demand': 0.0,
                'confidence_lower': 0.0,
                'confidence_upper': 0.0,
                'model_used': 'error_fallback',
                'seasonality_detected': False,
                'trend_direction': 'unknown',
                'forecast_accuracy_score': None,
                'error': str(e),
            }

    def calculate_forecast_accuracy(self, part_id: int) -> Optional[float]:
        """
        Calculate forecast accuracy using historical forecasts and actual consumption.

        Uses MAPE (Mean Absolute Percentage Error) metric.

        Args:
            part_id: ID of the part

        Returns:
            Accuracy score (0-1, higher is better), None if insufficient data
        """
        try:
            from ..models import ProcurementOutcome

            # Get recent outcomes with actual demand data (last 90 days)
            ninety_days_ago = datetime.now() - timedelta(days=90)
            outcomes = ProcurementOutcome.objects.filter(
                pipeline_execution__part_id=part_id,
                created_at__gte=ninety_days_ago,
                actual_demand__isnull=False,
                forecast_demand__gt=0,
            )

            if outcomes.count() < 3:
                # Insufficient data for accuracy calculation
                return None

            # Calculate MAPE
            total_ape = 0.0
            count = 0

            for outcome in outcomes:
                forecast = float(outcome.forecast_demand)
                actual = float(outcome.actual_demand)

                if forecast > 0:
                    ape = abs(actual - forecast) / forecast
                    total_ape += ape
                    count += 1

            if count == 0:
                return None

            mape = total_ape / count

            # Convert MAPE to accuracy score (1 - MAPE)
            # Cap at 0 (worst) and 1 (best)
            accuracy_score = max(0.0, min(1.0, 1.0 - mape))

            return accuracy_score

        except Exception as e:
            print(f'Error calculating forecast accuracy: {e}')
            return None
