"""Database models for Agentic AI Procurement System."""

import uuid
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from company.models import Company
from order.models import PurchaseOrder
from part.models import Part, PartCategory


class PipelineExecution(models.Model):
    """Tracks execution of procurement pipelines."""

    STATUS_CHOICES = [
        ('running', _('Running')),
        ('interrupted', _('Interrupted')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('rejected', _('Rejected')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='pipeline_executions',
        verbose_name=_('Part'),
    )
    trigger_reason = models.CharField(
        max_length=255, verbose_name=_('Trigger Reason')
    )
    trigger_timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Trigger Timestamp')
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='running', verbose_name=_('Status')
    )
    current_node = models.CharField(
        max_length=100, blank=True, verbose_name=_('Current Node')
    )
    state_data = models.JSONField(
        default=dict, blank=True, verbose_name=_('State Data')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Completed At')
    )
    error_message = models.TextField(
        blank=True, null=True, verbose_name=_('Error Message')
    )

    class Meta:
        """Model metadata."""

        verbose_name = _('Pipeline Execution')
        verbose_name_plural = _('Pipeline Executions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['part', 'status', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        """String representation."""
        return f'Pipeline {self.id} for {self.part.name} ({self.status})'


class DemandForecast(models.Model):
    """Stores demand forecast results."""

    MODEL_CHOICES = [
        ('prophet', _('Prophet')),
        ('xgboost', _('XGBoost')),
        ('simple_average', _('Simple Average')),
    ]

    TREND_CHOICES = [
        ('increasing', _('Increasing')),
        ('decreasing', _('Decreasing')),
        ('stable', _('Stable')),
        ('unknown', _('Unknown')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(
        PipelineExecution,
        on_delete=models.CASCADE,
        related_name='forecasts',
        verbose_name=_('Pipeline'),
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='demand_forecasts',
        verbose_name=_('Part'),
    )
    forecast_horizon_days = models.PositiveIntegerField(
        verbose_name=_('Forecast Horizon (Days)')
    )
    predicted_demand = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Predicted Demand'),
    )
    confidence_lower = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Confidence Lower Bound'),
    )
    confidence_upper = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Confidence Upper Bound'),
    )
    model_used = models.CharField(
        max_length=20, choices=MODEL_CHOICES, verbose_name=_('Model Used')
    )
    seasonality_detected = models.BooleanField(
        default=False, verbose_name=_('Seasonality Detected')
    )
    trend_direction = models.CharField(
        max_length=20, choices=TREND_CHOICES, verbose_name=_('Trend Direction')
    )
    forecast_accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Forecast Accuracy Score'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        """Model metadata."""

        verbose_name = _('Demand Forecast')
        verbose_name_plural = _('Demand Forecasts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['part', 'created_at']),
        ]

    def __str__(self):
        """String representation."""
        return f'Forecast for {self.part.name}: {self.predicted_demand} units'


class SupplierEvaluation(models.Model):
    """Stores supplier evaluation and ranking results."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(
        PipelineExecution,
        on_delete=models.CASCADE,
        related_name='supplier_evaluations',
        verbose_name=_('Pipeline'),
    )
    supplier = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='evaluations',
        verbose_name=_('Supplier'),
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='supplier_evaluations',
        verbose_name=_('Part'),
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Overall Score'),
    )
    price_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Price Score'),
    )
    lead_time_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Lead Time Score'),
    )
    reliability_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Reliability Score'),
    )
    moq_met = models.BooleanField(verbose_name=_('MOQ Met'))
    unit_price = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Unit Price'),
    )
    total_cost = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Total Cost'),
    )
    estimated_delivery_days = models.PositiveIntegerField(
        verbose_name=_('Estimated Delivery Days')
    )
    ranking_position = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name=_('Ranking Position')
    )
    recommendation_reason = models.TextField(
        verbose_name=_('Recommendation Reason')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        """Model metadata."""

        verbose_name = _('Supplier Evaluation')
        verbose_name_plural = _('Supplier Evaluations')
        ordering = ['pipeline', 'ranking_position']
        indexes = [
            models.Index(fields=['supplier', 'part']),
        ]

    def __str__(self):
        """String representation."""
        return f'{self.supplier.name} for {self.part.name}: Rank #{self.ranking_position}'


class ProcurementDecisionLog(models.Model):
    """Logs procurement decisions made by the Decision Agent."""

    DECISION_CHOICES = [
        ('ORDER', _('Order')),
        ('DO_NOT_ORDER', _('Do Not Order')),
        ('ESCALATE', _('Escalate')),
        ('ERROR', _('Error')),
    ]

    CONFIDENCE_CHOICES = [
        ('high', _('High')),
        ('medium', _('Medium')),
        ('low', _('Low')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(
        PipelineExecution,
        on_delete=models.CASCADE,
        related_name='decisions',
        verbose_name=_('Pipeline'),
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='procurement_decisions',
        verbose_name=_('Part'),
    )
    decision = models.CharField(
        max_length=20, choices=DECISION_CHOICES, verbose_name=_('Decision')
    )
    recommended_quantity = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Recommended Quantity'),
    )
    recommended_supplier = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recommended_decisions',
        verbose_name=_('Recommended Supplier'),
    )
    reasoning = models.TextField(verbose_name=_('Reasoning'))
    confidence_level = models.CharField(
        max_length=10, choices=CONFIDENCE_CHOICES, verbose_name=_('Confidence Level')
    )
    risk_factors = models.JSONField(
        default=list, blank=True, verbose_name=_('Risk Factors')
    )
    alternative_actions = models.JSONField(
        default=list, blank=True, verbose_name=_('Alternative Actions')
    )
    llm_model_used = models.CharField(
        max_length=50, blank=True, verbose_name=_('LLM Model Used')
    )
    llm_response_time_ms = models.PositiveIntegerField(
        default=0, verbose_name=_('LLM Response Time (ms)')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    class Meta:
        """Model metadata."""

        verbose_name = _('Procurement Decision Log')
        verbose_name_plural = _('Procurement Decision Logs')
        ordering = ['-created_at']

    def __str__(self):
        """String representation."""
        return f'{self.decision} for {self.part.name}: {self.recommended_quantity} units'


class ApprovalRequest(models.Model):
    """Tracks human approval requests for procurement decisions."""

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
        ('modified', _('Modified')),
        ('expired', _('Expired')),
    ]

    ACTION_CHOICES = [
        ('approve', _('Approve')),
        ('reject', _('Reject')),
        ('modify', _('Modify')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(
        PipelineExecution,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        verbose_name=_('Pipeline'),
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        verbose_name=_('Part'),
    )
    decision_log = models.ForeignKey(
        ProcurementDecisionLog,
        on_delete=models.CASCADE,
        related_name='approval_requests',
        verbose_name=_('Decision Log'),
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name=_('Status')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    expires_at = models.DateTimeField(verbose_name=_('Expires At'))
    responded_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Responded At')
    )
    responded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approval_responses',
        verbose_name=_('Responded By'),
    )
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        blank=True,
        null=True,
        verbose_name=_('Action'),
    )
    modified_quantity = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Modified Quantity'),
    )
    modified_supplier = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='modified_approvals',
        verbose_name=_('Modified Supplier'),
    )
    user_notes = models.TextField(blank=True, verbose_name=_('User Notes'))

    class Meta:
        """Model metadata."""

        verbose_name = _('Approval Request')
        verbose_name_plural = _('Approval Requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
        ]

    def __str__(self):
        """String representation."""
        return f'Approval for {self.part.name} ({self.status})'


class ProcurementOutcome(models.Model):
    """Tracks outcomes of procurement decisions for learning."""

    DECISION_CHOICES = [
        ('ORDER', _('Order')),
        ('DO_NOT_ORDER', _('Do Not Order')),
        ('ESCALATE', _('Escalate')),
        ('REJECTED', _('Rejected')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pipeline = models.ForeignKey(
        PipelineExecution,
        on_delete=models.CASCADE,
        related_name='outcomes',
        verbose_name=_('Pipeline'),
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='procurement_outcomes',
        verbose_name=_('Part'),
    )
    po = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procurement_outcomes',
        verbose_name=_('Purchase Order'),
    )
    decision_made = models.CharField(
        max_length=20, choices=DECISION_CHOICES, verbose_name=_('Decision Made')
    )
    quantity_ordered = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Quantity Ordered'),
    )
    supplier_used = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='procurement_outcomes',
        verbose_name=_('Supplier Used'),
    )
    forecast_demand = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Forecast Demand'),
    )
    actual_demand = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Actual Demand'),
    )
    forecast_error = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Forecast Error'),
    )
    delivery_on_time = models.BooleanField(
        null=True, blank=True, verbose_name=_('Delivery On Time')
    )
    delivery_date = models.DateField(
        null=True, blank=True, verbose_name=_('Delivery Date')
    )
    outcome_timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Outcome Timestamp')
    )
    learning_applied = models.BooleanField(
        default=False, verbose_name=_('Learning Applied')
    )

    class Meta:
        """Model metadata."""

        verbose_name = _('Procurement Outcome')
        verbose_name_plural = _('Procurement Outcomes')
        ordering = ['-outcome_timestamp']

    def __str__(self):
        """String representation."""
        return f'Outcome for {self.part.name}: {self.decision_made}'


class ProphetModelCache(models.Model):
    """Caches trained Prophet models for performance."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part = models.OneToOneField(
        Part,
        on_delete=models.CASCADE,
        related_name='prophet_model_cache',
        verbose_name=_('Part'),
    )
    model_binary = models.BinaryField(verbose_name=_('Model Binary'))
    training_data_hash = models.CharField(
        max_length=64, verbose_name=_('Training Data Hash')
    )
    training_date = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Training Date')
    )
    training_samples_count = models.PositiveIntegerField(
        validators=[MinValueValidator(1)], verbose_name=_('Training Samples Count')
    )
    model_performance_metrics = models.JSONField(
        default=dict, blank=True, verbose_name=_('Model Performance Metrics')
    )
    last_used = models.DateTimeField(
        auto_now=True, verbose_name=_('Last Used')
    )
    version = models.PositiveIntegerField(default=1, verbose_name=_('Version'))

    class Meta:
        """Model metadata."""

        verbose_name = _('Prophet Model Cache')
        verbose_name_plural = _('Prophet Model Caches')

    def __str__(self):
        """String representation."""
        return f'Prophet model for {self.part.name} (v{self.version})'


class ReorderPointHistory(models.Model):
    """Tracks reorder point adjustments over time."""

    ADJUSTED_BY_CHOICES = [
        ('system', _('System')),
        ('user', _('User')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='reorder_point_history',
        verbose_name=_('Part'),
    )
    old_reorder_point = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('Old Reorder Point'),
    )
    new_reorder_point = models.DecimalField(
        max_digits=19,
        decimal_places=6,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name=_('New Reorder Point'),
    )
    adjustment_reason = models.TextField(verbose_name=_('Adjustment Reason'))
    forecast_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Forecast Accuracy'),
    )
    stockout_count = models.PositiveIntegerField(
        default=0, verbose_name=_('Stockout Count')
    )
    adjustment_timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name=_('Adjustment Timestamp')
    )
    adjusted_by = models.CharField(
        max_length=10, choices=ADJUSTED_BY_CHOICES, verbose_name=_('Adjusted By')
    )

    class Meta:
        """Model metadata."""

        verbose_name = _('Reorder Point History')
        verbose_name_plural = _('Reorder Point Histories')
        ordering = ['-adjustment_timestamp']

    def __str__(self):
        """String representation."""
        return f'{self.part.name}: {self.old_reorder_point} → {self.new_reorder_point}'


class SupplierReliabilityScore(models.Model):
    """Tracks supplier reliability metrics for ranking."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='reliability_scores',
        verbose_name=_('Supplier'),
    )
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='supplier_reliability_scores',
        verbose_name=_('Part'),
    )
    on_time_delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('On-Time Delivery Rate'),
    )
    quality_acceptance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Quality Acceptance Rate'),
    )
    lead_time_accuracy = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
        verbose_name=_('Lead Time Accuracy'),
    )
    total_orders = models.PositiveIntegerField(
        default=0, verbose_name=_('Total Orders')
    )
    successful_orders = models.PositiveIntegerField(
        default=0, verbose_name=_('Successful Orders')
    )
    last_updated = models.DateTimeField(
        auto_now=True, verbose_name=_('Last Updated')
    )
    calculation_period_days = models.PositiveIntegerField(
        default=90, validators=[MinValueValidator(1)], verbose_name=_('Calculation Period (Days)')
    )

    class Meta:
        """Model metadata."""

        verbose_name = _('Supplier Reliability Score')
        verbose_name_plural = _('Supplier Reliability Scores')
        indexes = [
            models.Index(fields=['supplier', 'part']),
            models.Index(fields=['last_updated']),
        ]

    def __str__(self):
        """String representation."""
        part_str = f' for {self.part.name}' if self.part else ''
        return f'{self.supplier.name}{part_str}: {self.on_time_delivery_rate:.2%}'


class FewShotMemory(models.Model):
    """Stores few-shot examples for LLM context."""

    OUTCOME_QUALITY_CHOICES = [
        ('excellent', _('Excellent')),
        ('good', _('Good')),
        ('poor', _('Poor')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    part_category = models.ForeignKey(
        PartCategory,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='few_shot_memories',
        verbose_name=_('Part Category'),
    )
    decision_context = models.JSONField(verbose_name=_('Decision Context'))
    decision_made = models.CharField(max_length=20, verbose_name=_('Decision Made'))
    outcome_quality = models.CharField(
        max_length=10, choices=OUTCOME_QUALITY_CHOICES, verbose_name=_('Outcome Quality')
    )
    reasoning = models.TextField(verbose_name=_('Reasoning'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    usage_count = models.PositiveIntegerField(default=0, verbose_name=_('Usage Count'))
    last_used = models.DateTimeField(
        null=True, blank=True, verbose_name=_('Last Used')
    )

    class Meta:
        """Model metadata."""

        verbose_name = _('Few-Shot Memory')
        verbose_name_plural = _('Few-Shot Memories')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['part_category']),
            models.Index(fields=['outcome_quality']),
            models.Index(fields=['usage_count']),
        ]

    def __str__(self):
        """String representation."""
        category_str = f' in {self.part_category.name}' if self.part_category else ''
        return f'{self.decision_made}{category_str} ({self.outcome_quality})'
