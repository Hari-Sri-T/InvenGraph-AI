"""URL routing for AI-First Logistics Management System Web Interface."""

from django.urls import path
from django.views.generic import RedirectView

from . import views

app_name = 'ailms'

urlpatterns = [
    # Dashboard
    path('', RedirectView.as_view(pattern_name='ailms:dashboard-full', permanent=False), name='dashboard-redirect'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('dashboard-full/', views.DashboardView.as_view(), name='dashboard-full'),
    
    # Parts Management
    path('parts/', views.PartsListView.as_view(), name='parts_list'),
    path('parts/<int:part_id>/', views.PartDetailView.as_view(), name='part_detail'),
    
    # Procurement Pipeline
    path('procurement/pipelines/', views.PipelineListView.as_view(), name='pipeline-list'),
    path('procurement/pipeline/<uuid:pipeline_id>/', views.PipelineStatusView.as_view(), name='pipeline-status'),
    
    # Approval Queue
    path('approvals/', views.ApprovalQueueView.as_view(), name='approval-queue'),
    path('approvals/<uuid:request_id>/', views.ApprovalDetailView.as_view(), name='approval-detail'),
    
    # Supplier Management
    path('suppliers/', views.SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier-detail'),
    
    # Inventory Management
    path('inventory/', views.InventoryListView.as_view(), name='inventory-list'),
    path('inventory/<int:pk>/', views.InventoryDetailView.as_view(), name='inventory-detail'),
    
    # Analytics
    path('analytics/', views.AnalyticsDashboardView.as_view(), name='analytics'),
]
