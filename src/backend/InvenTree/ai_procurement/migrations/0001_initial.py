# Generated migration for agentic AI procurement models

import uuid
from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Initial migration for agentic AI procurement system."""

    initial = True

    dependencies = [
        ('part', '0001_initial'),
        ('company', '0001_initial'),
        ('order', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PipelineExecution',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('trigger_reason', models.CharField(max_length=255, verbose_name='Trigger Reason')),
                ('trigger_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Trigger Timestamp')),
                ('status', models.CharField(choices=[('running', 'Running'), ('interrupted', 'Interrupted'), ('completed', 'Completed'), ('failed', 'Failed'), ('rejected', 'Rejected')], default='running', max_length=20, verbose_name='Status')),
                ('current_node', models.CharField(blank=True, max_length=100, verbose_name='Current Node')),
                ('state_data', models.JSONField(blank=True, default=dict, verbose_name='State Data')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='Completed At')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='Error Message')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pipeline_executions', to='part.part', verbose_name='Part')),
            ],
            options={
                'verbose_name': 'Pipeline Execution',
                'verbose_name_plural': 'Pipeline Executions',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DemandForecast',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('forecast_horizon_days', models.PositiveIntegerField(verbose_name='Forecast Horizon (Days)')),
                ('predicted_demand', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Predicted Demand')),
                ('confidence_lower', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Confidence Lower Bound')),
                ('confidence_upper', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Confidence Upper Bound')),
                ('model_used', models.CharField(choices=[('prophet', 'Prophet'), ('xgboost', 'XGBoost'), ('simple_average', 'Simple Average')], max_length=20, verbose_name='Model Used')),
                ('seasonality_detected', models.BooleanField(default=False, verbose_name='Seasonality Detected')),
                ('trend_direction', models.CharField(choices=[('increasing', 'Increasing'), ('decreasing', 'Decreasing'), ('stable', 'Stable'), ('unknown', 'Unknown')], max_length=20, verbose_name='Trend Direction')),
                ('forecast_accuracy_score', models.DecimalField(blank=True, decimal_places=4, max_digits=5, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Forecast Accuracy Score')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='demand_forecasts', to='part.part', verbose_name='Part')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forecasts', to='ai_procurement.pipelineexecution', verbose_name='Pipeline')),
            ],
            options={
                'verbose_name': 'Demand Forecast',
                'verbose_name_plural': 'Demand Forecasts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SupplierEvaluation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('overall_score', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Overall Score')),
                ('price_score', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Price Score')),
                ('lead_time_score', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Lead Time Score')),
                ('reliability_score', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Reliability Score')),
                ('moq_met', models.BooleanField(verbose_name='MOQ Met')),
                ('unit_price', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Unit Price')),
                ('total_cost', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Total Cost')),
                ('estimated_delivery_days', models.PositiveIntegerField(verbose_name='Estimated Delivery Days')),
                ('ranking_position', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Ranking Position')),
                ('recommendation_reason', models.TextField(verbose_name='Recommendation Reason')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_evaluations', to='part.part', verbose_name='Part')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='supplier_evaluations', to='ai_procurement.pipelineexecution', verbose_name='Pipeline')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='evaluations', to='company.company', verbose_name='Supplier')),
            ],
            options={
                'verbose_name': 'Supplier Evaluation',
                'verbose_name_plural': 'Supplier Evaluations',
                'ordering': ['pipeline', 'ranking_position'],
            },
        ),
        migrations.CreateModel(
            name='ProcurementDecisionLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('decision', models.CharField(choices=[('ORDER', 'Order'), ('DO_NOT_ORDER', 'Do Not Order'), ('ESCALATE', 'Escalate'), ('ERROR', 'Error')], max_length=20, verbose_name='Decision')),
                ('recommended_quantity', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Recommended Quantity')),
                ('reasoning', models.TextField(verbose_name='Reasoning')),
                ('confidence_level', models.CharField(choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')], max_length=10, verbose_name='Confidence Level')),
                ('risk_factors', models.JSONField(blank=True, default=list, verbose_name='Risk Factors')),
                ('alternative_actions', models.JSONField(blank=True, default=list, verbose_name='Alternative Actions')),
                ('llm_model_used', models.CharField(blank=True, max_length=50, verbose_name='LLM Model Used')),
                ('llm_response_time_ms', models.PositiveIntegerField(default=0, verbose_name='LLM Response Time (ms)')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='procurement_decisions', to='part.part', verbose_name='Part')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='decisions', to='ai_procurement.pipelineexecution', verbose_name='Pipeline')),
                ('recommended_supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recommended_decisions', to='company.company', verbose_name='Recommended Supplier')),
            ],
            options={
                'verbose_name': 'Procurement Decision Log',
                'verbose_name_plural': 'Procurement Decision Logs',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ApprovalRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('modified', 'Modified'), ('expired', 'Expired')], default='pending', max_length=20, verbose_name='Status')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('expires_at', models.DateTimeField(verbose_name='Expires At')),
                ('responded_at', models.DateTimeField(blank=True, null=True, verbose_name='Responded At')),
                ('action', models.CharField(blank=True, choices=[('approve', 'Approve'), ('reject', 'Reject'), ('modify', 'Modify')], max_length=10, null=True, verbose_name='Action')),
                ('modified_quantity', models.DecimalField(blank=True, decimal_places=6, max_digits=19, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Modified Quantity')),
                ('user_notes', models.TextField(blank=True, verbose_name='User Notes')),
                ('decision_log', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_requests', to='ai_procurement.procurementdecisionlog', verbose_name='Decision Log')),
                ('modified_supplier', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_approvals', to='company.company', verbose_name='Modified Supplier')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_requests', to='part.part', verbose_name='Part')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_requests', to='ai_procurement.pipelineexecution', verbose_name='Pipeline')),
                ('responded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approval_responses', to=settings.AUTH_USER_MODEL, verbose_name='Responded By')),
            ],
            options={
                'verbose_name': 'Approval Request',
                'verbose_name_plural': 'Approval Requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ProcurementOutcome',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('decision_made', models.CharField(choices=[('ORDER', 'Order'), ('DO_NOT_ORDER', 'Do Not Order'), ('ESCALATE', 'Escalate'), ('REJECTED', 'Rejected')], max_length=20, verbose_name='Decision Made')),
                ('quantity_ordered', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Quantity Ordered')),
                ('forecast_demand', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Forecast Demand')),
                ('actual_demand', models.DecimalField(blank=True, decimal_places=6, max_digits=19, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Actual Demand')),
                ('forecast_error', models.DecimalField(blank=True, decimal_places=6, max_digits=19, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Forecast Error')),
                ('delivery_on_time', models.BooleanField(blank=True, null=True, verbose_name='Delivery On Time')),
                ('delivery_date', models.DateField(blank=True, null=True, verbose_name='Delivery Date')),
                ('outcome_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Outcome Timestamp')),
                ('learning_applied', models.BooleanField(default=False, verbose_name='Learning Applied')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='procurement_outcomes', to='part.part', verbose_name='Part')),
                ('pipeline', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='outcomes', to='ai_procurement.pipelineexecution', verbose_name='Pipeline')),
                ('po', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='procurement_outcomes', to='order.purchaseorder', verbose_name='Purchase Order')),
                ('supplier_used', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='procurement_outcomes', to='company.company', verbose_name='Supplier Used')),
            ],
            options={
                'verbose_name': 'Procurement Outcome',
                'verbose_name_plural': 'Procurement Outcomes',
                'ordering': ['-outcome_timestamp'],
            },
        ),
        migrations.CreateModel(
            name='ProphetModelCache',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('model_binary', models.BinaryField(verbose_name='Model Binary')),
                ('training_data_hash', models.CharField(max_length=64, verbose_name='Training Data Hash')),
                ('training_date', models.DateTimeField(auto_now_add=True, verbose_name='Training Date')),
                ('training_samples_count', models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)], verbose_name='Training Samples Count')),
                ('model_performance_metrics', models.JSONField(blank=True, default=dict, verbose_name='Model Performance Metrics')),
                ('last_used', models.DateTimeField(auto_now=True, verbose_name='Last Used')),
                ('version', models.PositiveIntegerField(default=1, verbose_name='Version')),
                ('part', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='prophet_model_cache', to='part.part', verbose_name='Part')),
            ],
            options={
                'verbose_name': 'Prophet Model Cache',
                'verbose_name_plural': 'Prophet Model Caches',
            },
        ),
        migrations.CreateModel(
            name='ReorderPointHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('old_reorder_point', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='Old Reorder Point')),
                ('new_reorder_point', models.DecimalField(decimal_places=6, max_digits=19, validators=[django.core.validators.MinValueValidator(Decimal('0'))], verbose_name='New Reorder Point')),
                ('adjustment_reason', models.TextField(verbose_name='Adjustment Reason')),
                ('forecast_accuracy', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Forecast Accuracy')),
                ('stockout_count', models.PositiveIntegerField(default=0, verbose_name='Stockout Count')),
                ('adjustment_timestamp', models.DateTimeField(auto_now_add=True, verbose_name='Adjustment Timestamp')),
                ('adjusted_by', models.CharField(choices=[('system', 'System'), ('user', 'User')], max_length=10, verbose_name='Adjusted By')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reorder_point_history', to='part.part', verbose_name='Part')),
            ],
            options={
                'verbose_name': 'Reorder Point History',
                'verbose_name_plural': 'Reorder Point Histories',
                'ordering': ['-adjustment_timestamp'],
            },
        ),
        migrations.CreateModel(
            name='SupplierReliabilityScore',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('on_time_delivery_rate', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='On-Time Delivery Rate')),
                ('quality_acceptance_rate', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Quality Acceptance Rate')),
                ('lead_time_accuracy', models.DecimalField(decimal_places=4, max_digits=5, validators=[django.core.validators.MinValueValidator(Decimal('0')), django.core.validators.MaxValueValidator(Decimal('1'))], verbose_name='Lead Time Accuracy')),
                ('total_orders', models.PositiveIntegerField(default=0, verbose_name='Total Orders')),
                ('successful_orders', models.PositiveIntegerField(default=0, verbose_name='Successful Orders')),
                ('last_updated', models.DateTimeField(auto_now=True, verbose_name='Last Updated')),
                ('calculation_period_days', models.PositiveIntegerField(default=90, validators=[django.core.validators.MinValueValidator(1)], verbose_name='Calculation Period (Days)')),
                ('part', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='supplier_reliability_scores', to='part.part', verbose_name='Part')),
                ('supplier', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reliability_scores', to='company.company', verbose_name='Supplier')),
            ],
            options={
                'verbose_name': 'Supplier Reliability Score',
                'verbose_name_plural': 'Supplier Reliability Scores',
            },
        ),
        migrations.CreateModel(
            name='FewShotMemory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('decision_context', models.JSONField(verbose_name='Decision Context')),
                ('decision_made', models.CharField(max_length=20, verbose_name='Decision Made')),
                ('outcome_quality', models.CharField(choices=[('excellent', 'Excellent'), ('good', 'Good'), ('poor', 'Poor')], max_length=10, verbose_name='Outcome Quality')),
                ('reasoning', models.TextField(verbose_name='Reasoning')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('usage_count', models.PositiveIntegerField(default=0, verbose_name='Usage Count')),
                ('last_used', models.DateTimeField(blank=True, null=True, verbose_name='Last Used')),
                ('part_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='few_shot_memories', to='part.partcategory', verbose_name='Part Category')),
            ],
            options={
                'verbose_name': 'Few-Shot Memory',
                'verbose_name_plural': 'Few-Shot Memories',
                'ordering': ['-created_at'],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name='pipelineexecution',
            index=models.Index(fields=['part', 'status', 'created_at'], name='ai_procurem_part_id_status_created_idx'),
        ),
        migrations.AddIndex(
            model_name='pipelineexecution',
            index=models.Index(fields=['status'], name='ai_procurem_status_idx'),
        ),
        migrations.AddIndex(
            model_name='pipelineexecution',
            index=models.Index(fields=['created_at'], name='ai_procurem_created_idx'),
        ),
        migrations.AddIndex(
            model_name='demandforecast',
            index=models.Index(fields=['part', 'created_at'], name='ai_procurem_forecast_part_created_idx'),
        ),
        migrations.AddIndex(
            model_name='supplierevaluation',
            index=models.Index(fields=['supplier', 'part'], name='ai_procurem_eval_supplier_part_idx'),
        ),
        migrations.AddIndex(
            model_name='approvalrequest',
            index=models.Index(fields=['status', 'expires_at'], name='ai_procurem_approval_status_expires_idx'),
        ),
        migrations.AddIndex(
            model_name='supplierreliabilityscore',
            index=models.Index(fields=['supplier', 'part'], name='ai_procurem_reliability_supplier_part_idx'),
        ),
        migrations.AddIndex(
            model_name='supplierreliabilityscore',
            index=models.Index(fields=['last_updated'], name='ai_procurem_reliability_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='fewshotmemory',
            index=models.Index(fields=['part_category'], name='ai_procurem_memory_category_idx'),
        ),
        migrations.AddIndex(
            model_name='fewshotmemory',
            index=models.Index(fields=['outcome_quality'], name='ai_procurem_memory_quality_idx'),
        ),
        migrations.AddIndex(
            model_name='fewshotmemory',
            index=models.Index(fields=['usage_count'], name='ai_procurem_memory_usage_idx'),
        ),
    ]
