"""Management command to create demo data for AI Procurement system."""

from decimal import Decimal
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User

from part.models import Part, PartCategory
from company.models import Company, SupplierPart
from stock.models import StockItem, StockLocation
from ai_procurement.models import (
    PipelineExecution,
    DemandForecast,
    SupplierEvaluation,
    ProcurementDecisionLog,
    ApprovalRequest,
    SupplierReliabilityScore,
    ProcurementOutcome,
)


class Command(BaseCommand):
    """Create demo data for AI Procurement system."""

    help = 'Creates demo data for testing the AI Procurement system'

    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing demo data before creating new data',
        )

    def handle(self, *args, **options):
        """Execute the command."""
        if options['clear']:
            self.stdout.write('Clearing existing demo data...')
            self.clear_demo_data()

        self.stdout.write('Creating demo data...')
        
        # Create categories
        categories = self.create_categories()
        
        # Create suppliers
        suppliers = self.create_suppliers()
        
        # Create parts
        parts = self.create_parts(categories)
        
        # Create supplier parts (pricing and lead times)
        self.create_supplier_parts(parts, suppliers)
        
        # Create stock locations and items
        locations = self.create_stock_locations()
        self.create_stock_items(parts, locations)
        
        # Create supplier reliability scores
        self.create_reliability_scores(suppliers, parts)
        
        # Create historical demand data
        self.create_historical_demand(parts)
        
        # Create past purchase orders
        self.create_past_purchase_orders(parts, suppliers)
        
        # Create pipeline executions with forecasts and evaluations
        pipelines = self.create_pipeline_executions(parts)
        self.create_forecasts(pipelines)
        self.create_supplier_evaluations(pipelines, suppliers)
        
        # Create decisions and approval requests
        self.create_decisions_and_approvals(pipelines, suppliers)
        
        # Create some completed outcomes
        self.create_outcomes(pipelines, suppliers)
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))

    def clear_demo_data(self):
        """Clear existing demo data."""
        ApprovalRequest.objects.all().delete()
        ProcurementDecisionLog.objects.all().delete()
        ProcurementOutcome.objects.all().delete()
        SupplierEvaluation.objects.all().delete()
        DemandForecast.objects.all().delete()
        PipelineExecution.objects.all().delete()
        SupplierReliabilityScore.objects.all().delete()
        self.stdout.write('Cleared existing demo data')

    def create_categories(self):
        """Create part categories."""
        categories = []
        category_names = [
            'Electronics',
            'Mechanical Components',
            'Raw Materials',
            'Fasteners',
            'Packaging',
        ]
        
        for name in category_names:
            category, created = PartCategory.objects.get_or_create(
                name=name,
                defaults={'description': f'{name} category'}
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {name}')
        
        return categories

    def create_suppliers(self):
        """Create supplier companies."""
        suppliers_data = [
            {'name': 'TechSupply Inc', 'description': 'Electronics and components supplier'},
            {'name': 'MechParts Ltd', 'description': 'Mechanical parts manufacturer'},
            {'name': 'FastShip Co', 'description': 'Quick delivery specialist'},
            {'name': 'BudgetParts', 'description': 'Cost-effective supplier'},
            {'name': 'Premium Components', 'description': 'High-quality premium parts'},
        ]
        
        suppliers = []
        for data in suppliers_data:
            supplier, created = Company.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'is_supplier': True,
                    'is_customer': False,
                }
            )
            suppliers.append(supplier)
            if created:
                self.stdout.write(f'Created supplier: {data["name"]}')
        
        return suppliers

    def create_parts(self, categories):
        """Create parts with varied stock requirements."""
        parts_data = [
            # Electronics - High volume
            {'name': 'Resistor 10K Ohm', 'description': '10K Ohm 1/4W resistor', 'category': 0, 'units': '', 'min_stock': 500, 'ipn': 'RES-10K-025W'},
            {'name': 'Capacitor 100uF', 'description': '100uF 25V electrolytic capacitor', 'category': 0, 'units': '', 'min_stock': 300, 'ipn': 'CAP-100UF-25V'},
            {'name': 'LED Red 5mm', 'description': '5mm red LED 20mA', 'category': 0, 'units': '', 'min_stock': 400, 'ipn': 'LED-RED-5MM'},
            {'name': 'Arduino Nano', 'description': 'Arduino Nano microcontroller', 'category': 0, 'units': '', 'min_stock': 50, 'ipn': 'MCU-NANO-V3'},
            {'name': 'USB Cable Type-C', 'description': 'USB Type-C cable 1m', 'category': 0, 'units': '', 'min_stock': 100, 'ipn': 'CBL-USBC-1M'},
            
            # Mechanical - Medium volume
            {'name': 'M4 Hex Bolt', 'description': 'M4x20mm stainless steel hex bolt', 'category': 3, 'units': '', 'min_stock': 1000, 'ipn': 'BLT-M4-20-SS'},
            {'name': 'M4 Nut', 'description': 'M4 stainless steel hex nut', 'category': 3, 'units': '', 'min_stock': 1000, 'ipn': 'NUT-M4-SS'},
            {'name': 'Bearing 608', 'description': '608 ball bearing 8x22x7mm', 'category': 1, 'units': '', 'min_stock': 100, 'ipn': 'BRG-608-STD'},
            {'name': 'Gear 20T', 'description': '20 tooth spur gear module 1', 'category': 1, 'units': '', 'min_stock': 50, 'ipn': 'GER-20T-M1'},
            {'name': 'Spring 10mm', 'description': 'Compression spring 10mm OD', 'category': 1, 'units': '', 'min_stock': 200, 'ipn': 'SPR-10MM-COMP'},
            
            # Raw Materials - Low volume
            {'name': 'Aluminum Sheet 1mm', 'description': '1mm aluminum sheet 1000x1000mm', 'category': 2, 'units': 'm**2', 'min_stock': 10, 'ipn': 'ALU-SHT-1MM'},
            {'name': 'Steel Rod 10mm', 'description': '10mm diameter steel rod', 'category': 2, 'units': '', 'min_stock': 20, 'ipn': 'STL-ROD-10MM'},
            {'name': 'Plastic Sheet ABS', 'description': '3mm ABS plastic sheet', 'category': 2, 'units': 'm**2', 'min_stock': 15, 'ipn': 'PLA-ABS-3MM'},
            
            # Packaging
            {'name': 'Cardboard Box Small', 'description': 'Shipping box 20x20x20cm', 'category': 4, 'units': '', 'min_stock': 200, 'ipn': 'BOX-SML-20CM'},
            {'name': 'Bubble Wrap', 'description': 'Bubble wrap roll 500mm x 50m', 'category': 4, 'units': '', 'min_stock': 50, 'ipn': 'PKG-BUBBLE-50M'},
        ]
        
        parts = []
        for data in parts_data:
            part, created = Part.objects.get_or_create(
                name=data['name'],
                defaults={
                    'description': data['description'],
                    'category': categories[data['category']],
                    'units': data['units'],
                    'IPN': data['ipn'],
                    'active': True,
                    'purchaseable': True,
                    'minimum_stock': data['min_stock'],
                }
            )
            parts.append(part)
            if created:
                self.stdout.write(f'Created part: {data["name"]}')
        
        return parts

    def create_supplier_parts(self, parts, suppliers):
        """Create supplier part relationships with pricing."""
        # Each part has 2-3 suppliers with different prices and lead times
        for part_idx, part in enumerate(parts):
            # Number of suppliers varies by part type
            num_suppliers = 3 if part_idx < 10 else 2
            
            for i, supplier in enumerate(suppliers[:num_suppliers]):
                # Price varies by part type and supplier
                if part_idx < 5:  # Electronics - moderate price
                    base_price = Decimal('5.00') + Decimal(i * 2)
                elif part_idx < 10:  # Mechanical/Fasteners - low price
                    base_price = Decimal('0.50') + Decimal(i * 0.20)
                else:  # Raw materials/Packaging - higher price
                    base_price = Decimal('25.00') + Decimal(i * 10)
                
                SupplierPart.objects.get_or_create(
                    part=part,
                    supplier=supplier,
                    defaults={
                        'SKU': f'{supplier.name[:3].upper()}-{part.IPN}',
                        'description': f'{part.name} from {supplier.name}',
                        'pack_quantity': '1',
                        'multiple': 1,
                    }
                )

    def create_stock_locations(self):
        """Create stock locations."""
        locations_data = [
            {'name': 'Warehouse A', 'description': 'Main warehouse'},
            {'name': 'Warehouse B', 'description': 'Secondary warehouse'},
            {'name': 'Production Floor', 'description': 'Manufacturing area'},
        ]
        
        locations = []
        for data in locations_data:
            location, created = StockLocation.objects.get_or_create(
                name=data['name'],
                defaults={'description': data['description']}
            )
            locations.append(location)
            if created:
                self.stdout.write(f'Created location: {data["name"]}')
        
        return locations

    def create_stock_items(self, parts, locations):
        """Create stock items with varied stock levels."""
        for idx, part in enumerate(parts):
            # Vary stock levels - some below minimum, some adequate, some critical
            min_stock = float(part.minimum_stock)
            
            if idx % 3 == 0:  # Critical - well below minimum
                quantity = int(min_stock * 0.2)
            elif idx % 3 == 1:  # Low - slightly below minimum
                quantity = int(min_stock * 0.7)
            else:  # Adequate - above minimum
                quantity = int(min_stock * 1.5)
            
            StockItem.objects.get_or_create(
                part=part,
                location=locations[0],
                defaults={'quantity': quantity}
            )

    def create_reliability_scores(self, suppliers, parts):
        """Create supplier reliability scores."""
        for supplier in suppliers:
            for part in parts[:3]:
                SupplierReliabilityScore.objects.get_or_create(
                    supplier=supplier,
                    part=part,
                    defaults={
                        'on_time_delivery_rate': Decimal('0.85') + Decimal(hash(supplier.name) % 15) / 100,
                        'quality_acceptance_rate': Decimal('0.90') + Decimal(hash(supplier.name) % 10) / 100,
                        'lead_time_accuracy': Decimal('0.80') + Decimal(hash(supplier.name) % 20) / 100,
                        'total_orders': 50,
                        'successful_orders': 45,
                    }
                )

    def create_pipeline_executions(self, parts):
        """Create pipeline executions in various states."""
        pipelines = []
        statuses = ['completed', 'running', 'interrupted', 'failed', 'completed', 'interrupted']
        nodes = ['', 'supplier_ranking', 'decision_agent', '', '', 'decision_agent']
        
        # Create pipelines for parts with low stock
        for i, part in enumerate(parts[:10]):
            # Vary the pipeline states
            status = statuses[i % len(statuses)]
            current_node = nodes[i % len(nodes)] if status == 'running' else ''
            
            # Vary trigger reasons
            if i % 4 == 0:
                trigger = 'Low stock detected'
            elif i % 4 == 1:
                trigger = 'Manual trigger'
            elif i % 4 == 2:
                trigger = 'Scheduled check'
            else:
                trigger = 'Stockout risk detected'
            
            # Vary completion level
            if status == 'completed':
                nodes_completed = ['demand_forecast', 'supplier_ranking', 'decision_agent', 'approval', 'execution', 'outcome_recording']
            elif status == 'interrupted':
                nodes_completed = ['demand_forecast', 'supplier_ranking', 'decision_agent']
            elif status == 'running':
                nodes_completed = ['demand_forecast'] if i % 2 == 0 else ['demand_forecast', 'supplier_ranking']
            else:
                nodes_completed = ['demand_forecast']
            
            pipeline = PipelineExecution.objects.create(
                part=part,
                trigger_reason=trigger,
                status=status,
                current_node=current_node,
                state_data={'nodes_completed': nodes_completed}
            )
            pipelines.append(pipeline)
            self.stdout.write(f'Created pipeline for {part.name} (status: {status})')
        
        return pipelines

    def create_forecasts(self, pipelines):
        """Create demand forecasts with varied predictions."""
        for idx, pipeline in enumerate(pipelines):
            # Vary forecast based on part type
            base_demand = float(pipeline.part.minimum_stock) * 1.2
            variation = (hash(pipeline.part.name) % 50) - 25
            predicted = Decimal(str(base_demand + variation))
            
            # Vary trend direction
            trends = ['increasing', 'decreasing', 'stable']
            trend = trends[idx % len(trends)]
            
            # Vary confidence intervals
            confidence_range = predicted * Decimal('0.15')
            
            DemandForecast.objects.create(
                pipeline=pipeline,
                part=pipeline.part,
                forecast_horizon_days=30,
                predicted_demand=predicted,
                confidence_lower=predicted - confidence_range,
                confidence_upper=predicted + confidence_range,
                model_used='prophet' if idx % 2 == 0 else 'arima',
                seasonality_detected=idx % 3 != 0,
                trend_direction=trend,
                forecast_accuracy_score=Decimal('0.80') + Decimal((idx % 15)) / 100,
            )

    def create_supplier_evaluations(self, pipelines, suppliers):
        """Create supplier evaluations."""
        for pipeline in pipelines:
            for rank, supplier in enumerate(suppliers[:3], 1):
                base_score = Decimal('0.90') - Decimal(rank * 0.05)
                SupplierEvaluation.objects.create(
                    pipeline=pipeline,
                    supplier=supplier,
                    part=pipeline.part,
                    overall_score=base_score,
                    price_score=base_score + Decimal('0.02'),
                    lead_time_score=base_score - Decimal('0.01'),
                    reliability_score=base_score + Decimal('0.01'),
                    moq_met=True,
                    unit_price=Decimal('12.50') + Decimal(rank * 2),
                    total_cost=Decimal('1875.00') + Decimal(rank * 300),
                    estimated_delivery_days=7 + rank * 2,
                    ranking_position=rank,
                    recommendation_reason=f'Rank #{rank}: Good balance of price and reliability',
                )

    def create_decisions_and_approvals(self, pipelines, suppliers):
        """Create procurement decisions and approval requests."""
        user = User.objects.first()
        
        for i, pipeline in enumerate(pipelines):
            if pipeline.status in ['interrupted', 'completed']:
                # Vary decision types
                if pipeline.status == 'interrupted':
                    decision_type = 'ESCALATE'
                elif i % 4 == 0:
                    decision_type = 'DEFER'
                else:
                    decision_type = 'ORDER'
                
                # Get forecast for this pipeline
                forecast = DemandForecast.objects.filter(pipeline=pipeline).first()
                recommended_qty = forecast.predicted_demand if forecast else Decimal('150.0')
                
                # Vary reasoning based on decision
                if decision_type == 'ORDER':
                    reasoning = f'Stock level critical. Forecast predicts {recommended_qty} units needed in 30 days. Recommended supplier has best overall score.'
                elif decision_type == 'DEFER':
                    reasoning = 'Current stock adequate for forecasted demand. Defer procurement to next cycle.'
                else:
                    reasoning = 'High uncertainty in demand forecast. Escalating to human review.'
                
                # Vary confidence and risk factors
                confidence_levels = ['high', 'medium', 'low']
                confidence = confidence_levels[i % len(confidence_levels)]
                
                risk_factors = []
                if i % 3 == 0:
                    risk_factors.append('Supplier lead time variability')
                if i % 3 == 1:
                    risk_factors.append('Demand forecast uncertainty')
                if i % 3 == 2:
                    risk_factors.append('Price volatility detected')
                
                decision = ProcurementDecisionLog.objects.create(
                    pipeline=pipeline,
                    part=pipeline.part,
                    decision=decision_type,
                    recommended_quantity=recommended_qty,
                    recommended_supplier=suppliers[i % len(suppliers)],
                    reasoning=reasoning,
                    confidence_level=confidence,
                    risk_factors=risk_factors if risk_factors else ['None identified'],
                    alternative_actions=['Order from backup supplier', 'Adjust order quantity', 'Wait for next cycle'],
                    llm_model_used='gpt-4' if i % 2 == 0 else 'claude-3',
                    llm_response_time_ms=1200 + (i * 100),
                )
                
                if pipeline.status == 'interrupted':
                    ApprovalRequest.objects.create(
                        pipeline=pipeline,
                        part=pipeline.part,
                        decision_log=decision,
                        status='pending',
                        expires_at=timezone.now() + timedelta(hours=24),
                    )

    def create_outcomes(self, pipelines, suppliers):
        """Create procurement outcomes with varied results."""
        for i, pipeline in enumerate(pipelines):
            if pipeline.status == 'completed':
                # Get the decision for this pipeline
                decision = ProcurementDecisionLog.objects.filter(pipeline=pipeline).first()
                
                if decision and decision.decision == 'ORDER':
                    # Vary actual demand vs forecast
                    forecast_demand = decision.recommended_quantity
                    # Some forecasts are accurate, some over/under predict
                    if i % 4 == 0:  # Accurate
                        actual_demand = forecast_demand * Decimal('0.98')
                    elif i % 4 == 1:  # Under-predicted
                        actual_demand = forecast_demand * Decimal('1.15')
                    elif i % 4 == 2:  # Over-predicted
                        actual_demand = forecast_demand * Decimal('0.80')
                    else:  # Very accurate
                        actual_demand = forecast_demand
                    
                    forecast_error = abs(forecast_demand - actual_demand)
                    
                    # Vary delivery performance
                    on_time = i % 5 != 0  # 80% on-time delivery
                    delivery_days = 7 if on_time else 10
                    
                    ProcurementOutcome.objects.create(
                        pipeline=pipeline,
                        part=pipeline.part,
                        decision_made='ORDER',
                        quantity_ordered=decision.recommended_quantity,
                        supplier_used=decision.recommended_supplier,
                        forecast_demand=forecast_demand,
                        actual_demand=actual_demand,
                        forecast_error=forecast_error,
                        delivery_on_time=on_time,
                        delivery_date=timezone.now().date() + timedelta(days=delivery_days),
                    )

    def create_historical_demand(self, parts):
        """Create historical demand data for forecasting."""
        # Note: InvenTree uses StockItemTracking with deltas field
        # For demo purposes, we'll skip creating historical tracking data
        # The AI system can work with current stock levels
        self.stdout.write('Skipped historical demand data (not required for demo)')
    
    def create_past_purchase_orders(self, parts, suppliers):
        """Create past purchase orders to show supplier reliability."""
        # Note: Creating completed POs is complex due to InvenTree's validation
        # The reliability scores are sufficient to demonstrate supplier tracking
        self.stdout.write('Skipped past purchase orders (reliability scores demonstrate supplier tracking)')
