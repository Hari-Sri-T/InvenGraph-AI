"""Django admin configuration for AI Procurement models."""

from django.contrib import admin

from .models import (
    ApprovalRequest,
    DemandForecast,
    FewShotMemory,
    PipelineExecution,
    ProcurementDecisionLog,
    ProcurementOutcome,
    ProphetModelCache,
    ReorderPointHistory,
    SupplierEvaluation,
    SupplierReliabilityScore,
)


@admin.register(PipelineExecution)
class PipelineExecutionAdmin(admin.ModelAdmin):
    """Admin interface for Pipeline Executions."""

    list_display = ['id', 'part', 'status', 'current_node', 'trigger_reason', 'created_at']
    list_filter = ['status', 'current_node', 'created_at']
    search_fields = ['id', 'part__name', 'trigger_reason']
    readonly_fields = ['id', 'created_at', 'updated_at', 'completed_at']
    date_hierarchy = 'created_at'


@admin.register(DemandForecast)
class DemandForecastAdmin(admin.ModelAdmin):
    """Admin interface for Demand Forecasts."""

    list_display = ['id', 'part', 'predicted_demand', 'model_used', 'trend_direction', 'created_at']
    list_filter = ['model_used', 'trend_direction', 'seasonality_detected', 'created_at']
    search_fields = ['part__name']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(SupplierEvaluation)
class SupplierEvaluationAdmin(admin.ModelAdmin):
    """Admin interface for Supplier Evaluations."""

    list_display = ['id', 'supplier', 'part', 'overall_score', 'ranking_position', 'created_at']
    list_filter = ['moq_met', 'created_at']
    search_fields = ['supplier__name', 'part__name']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(ProcurementDecisionLog)
class ProcurementDecisionLogAdmin(admin.ModelAdmin):
    """Admin interface for Procurement Decision Logs."""

    list_display = ['id', 'part', 'decision', 'recommended_quantity', 'recommended_supplier', 'confidence_level', 'created_at']
    list_filter = ['decision', 'confidence_level', 'created_at']
    search_fields = ['part__name', 'reasoning']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'created_at'


@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    """Admin interface for Approval Requests."""

    list_display = ['id', 'part', 'status', 'action', 'created_at', 'expires_at', 'responded_by']
    list_filter = ['status', 'action', 'created_at']
    search_fields = ['part__name', 'user_notes']
    readonly_fields = ['id', 'created_at', 'responded_at']
    date_hierarchy = 'created_at'


@admin.register(ProcurementOutcome)
class ProcurementOutcomeAdmin(admin.ModelAdmin):
    """Admin interface for Procurement Outcomes."""

    list_display = ['id', 'part', 'decision_made', 'quantity_ordered', 'supplier_used', 'learning_applied', 'outcome_timestamp']
    list_filter = ['decision_made', 'learning_applied', 'delivery_on_time', 'outcome_timestamp']
    search_fields = ['part__name']
    readonly_fields = ['id', 'outcome_timestamp']
    date_hierarchy = 'outcome_timestamp'


@admin.register(ProphetModelCache)
class ProphetModelCacheAdmin(admin.ModelAdmin):
    """Admin interface for Prophet Model Cache."""

    list_display = ['id', 'part', 'version', 'training_date', 'training_samples_count', 'last_used']
    list_filter = ['training_date', 'last_used']
    search_fields = ['part__name']
    readonly_fields = ['id', 'training_date', 'last_used']


@admin.register(ReorderPointHistory)
class ReorderPointHistoryAdmin(admin.ModelAdmin):
    """Admin interface for Reorder Point History."""

    list_display = ['id', 'part', 'old_reorder_point', 'new_reorder_point', 'adjusted_by', 'adjustment_timestamp']
    list_filter = ['adjusted_by', 'adjustment_timestamp']
    search_fields = ['part__name', 'adjustment_reason']
    readonly_fields = ['id', 'adjustment_timestamp']
    date_hierarchy = 'adjustment_timestamp'


@admin.register(SupplierReliabilityScore)
class SupplierReliabilityScoreAdmin(admin.ModelAdmin):
    """Admin interface for Supplier Reliability Scores."""

    list_display = ['id', 'supplier', 'part', 'on_time_delivery_rate', 'quality_acceptance_rate', 'total_orders', 'last_updated']
    list_filter = ['last_updated']
    search_fields = ['supplier__name', 'part__name']
    readonly_fields = ['id', 'last_updated']


@admin.register(FewShotMemory)
class FewShotMemoryAdmin(admin.ModelAdmin):
    """Admin interface for Few-Shot Memory."""

    list_display = ['id', 'part_category', 'decision_made', 'outcome_quality', 'usage_count', 'created_at']
    list_filter = ['outcome_quality', 'created_at']
    search_fields = ['decision_made', 'reasoning']
    readonly_fields = ['id', 'created_at', 'last_used']
    date_hierarchy = 'created_at'
