"""Supplier Agent: Ranks suppliers using multi-criteria decision analysis."""

from decimal import Decimal
from typing import Dict, List

from company.models import Company, SupplierPart
from part.models import Part

from ..logging_config import log_agent_output, log_error, logger
from ..models import SupplierReliabilityScore
from ..notifications import NotificationService


class CriteriaWeights:
    """Configurable weights for supplier ranking criteria."""

    def __init__(
        self,
        price_weight: float = 0.4,
        lead_time_weight: float = 0.3,
        reliability_weight: float = 0.3,
    ):
        """
        Initialize criteria weights.

        Args:
            price_weight: Weight for price criterion (default 0.4)
            lead_time_weight: Weight for lead time criterion (default 0.3)
            reliability_weight: Weight for reliability criterion (default 0.3)
        """
        # Validate weights sum to 1.0
        total = price_weight + lead_time_weight + reliability_weight
        if abs(total - 1.0) > 0.01:
            raise ValueError(f'Weights must sum to 1.0, got {total}')

        self.price_weight = price_weight
        self.lead_time_weight = lead_time_weight
        self.reliability_weight = reliability_weight


class SupplierAgent:
    """Agent responsible for ranking suppliers using multi-criteria analysis."""

    def __init__(self, criteria_weights: CriteriaWeights = None):
        """
        Initialize Supplier Agent.

        Args:
            criteria_weights: Custom criteria weights (optional)
        """
        self.criteria_weights = criteria_weights or CriteriaWeights()

    def get_supplier_reliability(
        self, supplier_id: int, part_id: int = None
    ) -> float:
        """
        Get supplier reliability score from learning layer.

        Args:
            supplier_id: ID of the supplier
            part_id: ID of the part (optional, for part-specific reliability)

        Returns:
            Reliability score between 0 and 1 (default 0.5 if no data)
        """
        try:
            if part_id:
                # Try to get part-specific reliability
                score = SupplierReliabilityScore.objects.get(
                    supplier_id=supplier_id, part_id=part_id
                )
            else:
                # Get general supplier reliability
                score = SupplierReliabilityScore.objects.filter(
                    supplier_id=supplier_id, part__isnull=True
                ).first()

            if score:
                # Average of all reliability metrics
                avg_reliability = (
                    float(score.on_time_delivery_rate)
                    + float(score.quality_acceptance_rate)
                    + float(score.lead_time_accuracy)
                ) / 3.0
                return avg_reliability

        except SupplierReliabilityScore.DoesNotExist:
            pass
        except Exception as e:
            print(f'Error getting supplier reliability: {e}')

        # Default reliability score if no historical data
        return 0.5

    def calculate_unit_price(
        self, supplier_part: SupplierPart, quantity: float
    ) -> float:
        """
        Calculate unit price considering quantity breaks.

        Args:
            supplier_part: SupplierPart instance
            quantity: Required quantity

        Returns:
            Unit price for the given quantity
        """
        # For now, use base price
        # TODO: Implement quantity break logic when available
        base_price = supplier_part.unit_price or Decimal('0')
        return float(base_price)

    def normalize_scores(
        self, values: List[float], reverse: bool = False
    ) -> List[float]:
        """
        Normalize scores to 0-1 range.

        Args:
            values: List of values to normalize
            reverse: If True, lower values get higher scores (for price, lead time)

        Returns:
            List of normalized scores
        """
        if not values or len(values) == 0:
            return []

        min_val = min(values)
        max_val = max(values)

        # Handle case where all values are the same
        if max_val == min_val:
            return [1.0] * len(values)

        normalized = []
        for val in values:
            if reverse:
                # Lower is better (price, lead time)
                score = 1.0 - ((val - min_val) / (max_val - min_val))
            else:
                # Higher is better (reliability)
                score = (val - min_val) / (max_val - min_val)
            normalized.append(score)

        return normalized

    def generate_recommendation_reason(
        self,
        supplier_name: str,
        price_score: float,
        lead_time_score: float,
        reliability_score: float,
        moq_met: bool,
    ) -> str:
        """
        Generate human-readable recommendation reason.

        Args:
            supplier_name: Name of the supplier
            price_score: Normalized price score
            lead_time_score: Normalized lead time score
            reliability_score: Normalized reliability score
            moq_met: Whether MOQ constraint is met

        Returns:
            Recommendation reason string
        """
        strengths = []
        if price_score > 0.7:
            strengths.append('competitive pricing')
        if lead_time_score > 0.7:
            strengths.append('fast delivery')
        if reliability_score > 0.7:
            strengths.append('high reliability')

        if not moq_met:
            return f'{supplier_name}: MOQ not met for required quantity'

        if strengths:
            return f'{supplier_name}: Strong in {", ".join(strengths)}'
        else:
            return f'{supplier_name}: Balanced across all criteria'

    def rank_suppliers(
        self, part_id: int, required_quantity: float
    ) -> List[Dict]:
        """
        Rank suppliers for a part using multi-criteria analysis.

        Args:
            part_id: ID of the part
            required_quantity: Required quantity to order

        Returns:
            List of supplier rankings sorted by overall score
        """
        try:
            # Get all suppliers for this part
            supplier_parts = SupplierPart.objects.filter(part_id=part_id).select_related(
                'supplier', 'part'
            )

            if not supplier_parts.exists():
                error_msg = (
                    f'No suppliers found for part {part_id}. '
                    f'Please add suppliers for this part in the InvenTree admin interface.'
                )
                logger.error(error_msg)

                # Send notification to responsible users
                try:
                    part = Part.objects.get(pk=part_id)
                    notification_service = NotificationService()
                    # TODO: Send notification to part responsible owner
                    logger.info(f'Notification sent for missing suppliers (part {part_id})')
                except Exception as notif_error:
                    logger.error(f'Failed to send notification: {notif_error}')

                raise Exception(error_msg)

            rankings = []
            prices = []
            lead_times = []
            reliabilities = []

            # First pass: collect all values for normalization
            for sp in supplier_parts:
                try:
                    unit_price = self.calculate_unit_price(sp, required_quantity)
                    lead_time_days = sp.lead_time or 30  # Default 30 days
                    reliability = self.get_supplier_reliability(sp.supplier.id, part_id)

                    prices.append(unit_price)
                    lead_times.append(lead_time_days)
                    reliabilities.append(reliability)
                except Exception as sp_error:
                    logger.error(
                        f'Error processing supplier {sp.supplier.id} for part {part_id}: {sp_error}'
                    )
                    # Use default values
                    prices.append(0.0)
                    lead_times.append(30)
                    reliabilities.append(0.5)

            # Normalize scores
            price_scores = self.normalize_scores(prices, reverse=True)
            lead_time_scores = self.normalize_scores(lead_times, reverse=True)
            reliability_scores = reliabilities  # Already 0-1

            # Second pass: calculate overall scores
            for idx, sp in enumerate(supplier_parts):
                try:
                    # Check MOQ constraint
                    moq = sp.minimum_order_quantity or Decimal('0')
                    moq_met = required_quantity >= float(moq)

                    # Calculate overall weighted score
                    overall_score = (
                        price_scores[idx] * self.criteria_weights.price_weight
                        + lead_time_scores[idx] * self.criteria_weights.lead_time_weight
                        + reliability_scores[idx] * self.criteria_weights.reliability_weight
                    )

                    # Calculate total cost
                    unit_price = prices[idx]
                    total_cost = unit_price * required_quantity

                    # Generate recommendation reason
                    reason = self.generate_recommendation_reason(
                        sp.supplier.name,
                        price_scores[idx],
                        lead_time_scores[idx],
                        reliability_scores[idx],
                        moq_met,
                    )

                    ranking = {
                        'supplier_id': sp.supplier.id,
                        'supplier_name': sp.supplier.name,
                        'overall_score': round(overall_score, 4),
                        'price_score': round(price_scores[idx], 4),
                        'lead_time_score': round(lead_time_scores[idx], 4),
                        'reliability_score': round(reliability_scores[idx], 4),
                        'moq_met': moq_met,
                        'unit_price': round(unit_price, 2),
                        'total_cost': round(total_cost, 2),
                        'estimated_delivery_days': int(lead_times[idx]),
                        'recommendation_reason': reason,
                    }

                    rankings.append(ranking)
                except Exception as ranking_error:
                    logger.error(
                        f'Error calculating ranking for supplier {sp.supplier.id}: {ranking_error}'
                    )
                    continue

            if not rankings:
                raise Exception(f'Failed to rank any suppliers for part {part_id}')

            # Sort by overall score (descending)
            rankings.sort(key=lambda r: r['overall_score'], reverse=True)

            # Assign ranking positions
            for idx, ranking in enumerate(rankings):
                ranking['ranking_position'] = idx + 1

            logger.info(
                f'Ranked {len(rankings)} suppliers for part {part_id}, '
                f'top supplier: {rankings[0]["supplier_name"]} '
                f'(score: {rankings[0]["overall_score"]})'
            )

            return rankings

        except Exception as e:
            log_error(
                pipeline_id='unknown',
                part_id=part_id,
                component='SupplierAgent',
                error_message=f'Supplier ranking failed: {str(e)}',
                error_details={'required_quantity': required_quantity},
            )
            raise
