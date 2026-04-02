"""URL routing for Agentic AI Procurement System."""

from django.urls import path

from . import views

app_name = 'ai_procurement'

urlpatterns = [
    # Legacy endpoints (backward compatibility)
    path('run/', views.ProcurementRunView.as_view(), name='ai-procurement-run'),
    path('approve/', views.ProcurementApproveView.as_view(), name='ai-procurement-approve'),
    # New agentic endpoints
    path(
        'pipeline/trigger/',
        views.PipelineTriggerView.as_view(),
        name='ai-procurement-pipeline-trigger',
    ),
    path(
        'pipeline/status/<str:pipeline_id>/',
        views.PipelineStatusView.as_view(),
        name='ai-procurement-pipeline-status',
    ),
    path(
        'pipeline/status/',
        views.PipelineStatusView.as_view(),
        name='ai-procurement-pipeline-status-list',
    ),
    path(
        'approvals/',
        views.ApprovalRequestListView.as_view(),
        name='ai-procurement-approvals-list',
    ),
    path(
        'approvals/<str:request_id>/action/',
        views.ApprovalActionView.as_view(),
        name='ai-procurement-approval-action',
    ),
]