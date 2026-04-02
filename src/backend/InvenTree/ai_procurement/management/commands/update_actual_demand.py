"""Management command to update actual demand for procurement outcomes."""

from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Sum

from ai_procurement.models import ProcurementOutcome
from stock.models import StockItemTracking


class Command(BaseCommand):
    """Update actual demand for procurement outcomes."""

    help = 'Update actual demand tracking and forecast error calculation'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to look back for outcomes to update',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        days = options['days']
        cutoff_date = datetime.now() - timedelta(days=days)

        self.stdout.write(f'Updating actual demand for outcomes from last {days} days...')

        # Get outcomes that need updating
        outcomes = ProcurementOutcome.objects.filter(
            created_at__gte=cutoff_date, actual_demand__isnull=True
        )

        updated_count = 0
        error_count = 0

        for outcome in outcomes:
            try:
                # Calculate actual consumption between order date and forecast period end
                order_date = outcome.outcome_timestamp
                forecast_end_date = order_date + timedelta(
                    days=30
                )  # Assuming 30-day forecast

                # Get actual consumption from stock tracking
                stock_movements = StockItemTracking.objects.filter(
                    item__part_id=outcome.part_id,
                    date__gte=order_date,
                    date__lte=forecast_end_date,
                    quantity__lt=0,  # Negative = consumption
                )

                actual_consumption = abs(
                    stock_movements.aggregate(total=Sum('quantity'))['total'] or 0
                )

                # Calculate forecast error
                forecast_error = abs(
                    float(outcome.forecast_demand) - float(actual_consumption)
                )

                # Update outcome
                outcome.actual_demand = actual_consumption
                outcome.forecast_error = forecast_error
                outcome.save()

                updated_count += 1

                if updated_count % 10 == 0:
                    self.stdout.write(f'Updated {updated_count} outcomes...')

            except Exception as e:
                error_count += 1
                self.stderr.write(
                    f'Error updating outcome {outcome.id}: {e}'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully updated {updated_count} outcomes '
                f'({error_count} errors)'
            )
        )
