"""Learning Layer: Continuous improvement through model retraining and optimization."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional

from django.db.models import Avg, Count, Q

from order.models import PurchaseOrder
from part.models import Part

from ..models import (
    FewShotMemory,
    PipelineExecution,
    ProcurementOutcome,
    ReorderPointHistory,
    SupplierReliabilityScore,
)


class LearningLayer:
    """Manages continuous learning and system improvement."""

    EMA_ALPHA = 0.3  # Exponential moving average smoothing factor
    CALCULATION_PERIOD_DAYS = 90

    def __init__(self):
        """Initialize Learning Layer."""
        pass

    def log_outcome(self, pipeline_id: str, outcome_data: Dict):
        """
        Log procurement outcome for learning.

        Args:
            pipeline_id: UUID of the pipeline execution
            outcome_data: Dictionary with outcome data
        """
        try:
            # Get pipeline execution
            pipeline = PipelineExecution.objects.get(id=pipeline_id)

            # Get forecast from pipeline state
            state_data = pipeline.state_data or {}
            forecast = state_data.get('forecast', {})

            # Create outcome record
            outcome = ProcurementOutcome.objects.create(
                pipeline=pipeline,
                part_id=pipeline.part_id,
                po_id=outcome_data.get('po_id'),
                decision_made=outcome_data['decision_made'],
                quantity_ordered=outcome_data.get('quantity_ordered', 0),
                supplier_used_id=outcome_data.get('supplier_used'),
                forecast_demand=forecast.get('predicted_demand', 0),
            )

            print(f'Logged outcome for pipeline {pipeline_id}')

            # Schedule async tasks for learning updates
            # Note: In production, these should be Celery/Django-Q tasks
            if outcome_data['decision_made'] == 'ORDER':
                self.schedule_prophet_retrain(pipeline.part_id)
                self.update_ema_trends(pipeline.part_id)
                self.adjust_reorder_point(pipeline.part_id)

        except Exception as e:
            print(f'Error logging outcome: {e}')

    def schedule_prophet_retrain(self, part_id: int):
        """
        Schedule Prophet model retraining (async).

        Args:
            part_id: ID of the part
        """
        try:
            # Try to use Celery task if available
            from ..tasks import retrain_prophet_model_async

            retrain_prophet_model_async.delay(part_id)
            print(f'Scheduled Prophet retraining task for part {part_id}')
        except ImportError:
            # Celery not available, run synchronously
            print(f'Celery not available, retraining Prophet synchronously for part {part_id}')
            self.retrain_prophet_model(part_id)

    def retrain_prophet_model(self, part_id: int):
        """
        Retrain Prophet model with latest data.

        Args:
            part_id: ID of the part
        """
        try:
            from ..agents.demand_agent import DemandAgent

            demand_agent = DemandAgent()

            # Get latest historical data
            historical_data = demand_agent.get_historical_consumption(
                part_id, lookback_days=DemandAgent.LOOKBACK_DAYS
            )

            # Check if sufficient data
            non_zero_days = (historical_data['y'] > 0).sum()
            if non_zero_days < DemandAgent.MIN_DATA_POINTS:
                print(f'Insufficient data for retraining part {part_id}')
                return

            # Train new model
            model = demand_agent.train_prophet_model(historical_data)

            # Cache the new model (this will increment version)
            demand_agent.cache_prophet_model(part_id, model, historical_data)

            print(f'Successfully retrained Prophet model for part {part_id}')

        except Exception as e:
            print(f'Error retraining Prophet model: {e}')

    def update_ema_trends(self, part_id: int):
        """
        Update exponential moving average trends.

        Args:
            part_id: ID of the part
        """
        try:
            # Get recent consumption data (last 7 days)
            from ..agents.demand_agent import DemandAgent

            demand_agent = DemandAgent()
            recent_data = demand_agent.get_historical_consumption(part_id, lookback_days=7)

            if len(recent_data) > 0:
                # Calculate EMA
                # Note: This is a simplified implementation
                # In production, store EMA state in database
                avg_consumption = recent_data['y'].mean()
                print(f'Updated EMA trends for part {part_id}: {avg_consumption:.2f}')

        except Exception as e:
            print(f'Error updating EMA trends: {e}')

    def adjust_reorder_point(self, part_id: int):
        """
        Adjust reorder point based on forecast accuracy and stockouts.

        Args:
            part_id: ID of the part
        """
        try:
            part = Part.objects.get(pk=part_id)
            current_reorder_point = float(part.minimum_stock or 0)

            if current_reorder_point <= 0:
                return  # No reorder point set

            # Calculate forecast accuracy
            forecast_accuracy = self.calculate_forecast_accuracy(part_id)

            # Count recent stockouts
            stockout_count = self.count_recent_stockouts(part_id, days=90)

            # Determine adjustment
            adjustment_factor = 1.0
            adjustment_reason = ''

            if forecast_accuracy is not None:
                if forecast_accuracy < 0.7 or stockout_count > 2:
                    # Increase reorder point (system underestimating)
                    adjustment_factor = 1.2
                    adjustment_reason = (
                        f'Low forecast accuracy ({forecast_accuracy:.2f}) '
                        f'or frequent stockouts ({stockout_count})'
                    )
                elif forecast_accuracy > 0.9 and stockout_count == 0:
                    # Decrease reorder point (system overestimating)
                    adjustment_factor = 0.9
                    adjustment_reason = (
                        f'High forecast accuracy ({forecast_accuracy:.2f}) '
                        f'and no stockouts'
                    )
                else:
                    adjustment_reason = 'Forecast accuracy within acceptable range'

            if adjustment_factor != 1.0:
                new_reorder_point = current_reorder_point * adjustment_factor

                # Bound adjustments (between 0 and 10x current value)
                new_reorder_point = max(0, min(new_reorder_point, current_reorder_point * 10))

                # Update part
                part.minimum_stock = Decimal(str(new_reorder_point))
                part.save()

                # Log adjustment
                ReorderPointHistory.objects.create(
                    part=part,
                    old_reorder_point=Decimal(str(current_reorder_point)),
                    new_reorder_point=Decimal(str(new_reorder_point)),
                    adjustment_reason=adjustment_reason,
                    forecast_accuracy=Decimal(str(forecast_accuracy or 0)),
                    stockout_count=stockout_count,
                    adjusted_by='system',
                )

                print(
                    f'Adjusted reorder point for part {part_id}: '
                    f'{current_reorder_point:.2f} → {new_reorder_point:.2f}'
                )

        except Part.DoesNotExist:
            print(f'Part {part_id} not found')
        except Exception as e:
            print(f'Error adjusting reorder point: {e}')

    def calculate_forecast_accuracy(self, part_id: int) -> Optional[float]:
        """
        Calculate forecast accuracy for a part.

        Args:
            part_id: ID of the part

        Returns:
            Forecast accuracy score (0-1) or None if insufficient data
        """
        try:
            # Get outcomes with actual demand data
            outcomes = ProcurementOutcome.objects.filter(
                part_id=part_id,
                actual_demand__isnull=False,
                forecast_demand__gt=0,
            ).order_by('-outcome_timestamp')[:10]  # Last 10 outcomes

            if not outcomes.exists():
                return None

            # Calculate MAPE (Mean Absolute Percentage Error)
            errors = []
            for outcome in outcomes:
                actual = float(outcome.actual_demand)
                forecast = float(outcome.forecast_demand)

                if actual > 0:
                    error = abs(forecast - actual) / actual
                    errors.append(error)

            if not errors:
                return None

            mape = sum(errors) / len(errors)
            accuracy = 1.0 - min(mape, 1.0)  # Convert error to accuracy

            return accuracy

        except Exception as e:
            print(f'Error calculating forecast accuracy: {e}')
            return None

    def count_recent_stockouts(self, part_id: int, days: int = 90) -> int:
        """
        Count recent stockouts for a part.

        Args:
            part_id: ID of the part
            days: Number of days to look back

        Returns:
            Number of stockouts
        """
        try:
            # TODO: Implement stockout detection logic
            # This would query StockItemTracking for periods where stock was 0
            # For now, return 0
            return 0

        except Exception as e:
            print(f'Error counting stockouts: {e}')
            return 0

    def update_supplier_reliability(
        self, supplier_id: int, part_id: int, pipeline_id: str
    ):
        """
        Update supplier reliability scores.

        Args:
            supplier_id: ID of the supplier
            part_id: ID of the part
            pipeline_id: UUID of the pipeline execution
        """
        try:
            # Get recent purchase orders for this supplier and part
            cutoff_date = datetime.now() - timedelta(days=self.CALCULATION_PERIOD_DAYS)

            pos = PurchaseOrder.objects.filter(
                supplier_id=supplier_id,
                lines__part__part_id=part_id,
                creation_date__gte=cutoff_date,
            ).distinct()

            if not pos.exists():
                return

            # Calculate metrics
            total_orders = pos.count()
            completed_orders = pos.filter(status=30).count()  # 30 = Complete

            # On-time delivery rate
            on_time_count = 0
            for po in pos.filter(status=30):
                if po.target_date and po.complete_date:
                    if po.complete_date <= po.target_date:
                        on_time_count += 1

            on_time_rate = on_time_count / total_orders if total_orders > 0 else 0.5

            # Quality acceptance rate (simplified - assume all accepted for now)
            quality_rate = 0.95

            # Lead time accuracy (simplified)
            lead_time_accuracy = 0.85

            # Update or create reliability score
            SupplierReliabilityScore.objects.update_or_create(
                supplier_id=supplier_id,
                part_id=part_id,
                defaults={
                    'on_time_delivery_rate': Decimal(str(on_time_rate)),
                    'quality_acceptance_rate': Decimal(str(quality_rate)),
                    'lead_time_accuracy': Decimal(str(lead_time_accuracy)),
                    'total_orders': total_orders,
                    'successful_orders': completed_orders,
                    'calculation_period_days': self.CALCULATION_PERIOD_DAYS,
                },
            )

            print(
                f'Updated supplier reliability for supplier {supplier_id}, part {part_id}'
            )

        except Exception as e:
            print(f'Error updating supplier reliability: {e}')

    def store_few_shot_example(
        self, decision_context: Dict, decision_made: str, reasoning: str, outcome_quality: str
    ):
        """
        Store few-shot example for LLM context.

        Args:
            decision_context: Decision context dictionary
            decision_made: Decision that was made
            reasoning: Reasoning for the decision
            outcome_quality: Quality of the outcome ('excellent', 'good', 'poor')
        """
        try:
            # Only store good/excellent outcomes
            if outcome_quality not in ['excellent', 'good']:
                return

            part_category_id = decision_context.get('part_category_id')

            FewShotMemory.objects.create(
                part_category_id=part_category_id,
                decision_context=decision_context,
                decision_made=decision_made,
                outcome_quality=outcome_quality,
                reasoning=reasoning,
            )

            print(f'Stored few-shot example: {decision_made} ({outcome_quality})')

        except Exception as e:
            print(f'Error storing few-shot example: {e}')
