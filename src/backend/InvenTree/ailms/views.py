"""Views for AI-First Logistics Management System Web Interface."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta

from ai_procurement.models import (
    PipelineExecution,
    ApprovalRequest,
    ProcurementDecisionLog,
    DemandForecast,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """AI Dashboard view."""
    
    template_name = 'ailms/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get dashboard metrics
        context['active_pipelines'] = PipelineExecution.objects.filter(
            status='running'
        ).count()
        
        context['pending_approvals'] = ApprovalRequest.objects.filter(
            status='pending',
            expires_at__gt=timezone.now()
        ).count()
        
        context['recent_decisions'] = ProcurementDecisionLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        # Calculate forecast accuracy
        recent_forecasts = DemandForecast.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30),
            forecast_accuracy_score__isnull=False
        )
        if recent_forecasts.exists():
            from django.db.models import Avg
            avg_accuracy = recent_forecasts.aggregate(avg=Avg('forecast_accuracy_score'))['avg']
            context['forecast_accuracy'] = float(avg_accuracy or 0)
        else:
            context['forecast_accuracy'] = 0
        
        # Get recent pipelines
        context['recent_pipelines'] = PipelineExecution.objects.select_related('part').order_by('-created_at')[:5]
        
        return context


class PartsListView(LoginRequiredMixin, TemplateView):
    """Parts list view with AI insights."""
    
    template_name = 'ailms/parts_list.html'
    
    def get_context_data(self, **kwargs):
        from part.models import Part
        from company.models import SupplierPart
        from django.db.models import Q, Prefetch
        
        context = super().get_context_data(**kwargs)
        
        # Get search query
        search_query = self.request.GET.get('search', '')
        
        # Build parts query with AI insights
        parts_query = Part.objects.filter(active=True).select_related('category')
        
        if search_query:
            parts_query = parts_query.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(IPN__icontains=search_query)
            )
        
        # Prefetch latest forecast for each part
        parts_query = parts_query.prefetch_related(
            Prefetch(
                'demand_forecasts',
                queryset=DemandForecast.objects.order_by('-created_at')[:1],
                to_attr='latest_forecast'
            ),
            Prefetch(
                'supplier_parts',
                queryset=SupplierPart.objects.select_related('supplier')
            )
        )
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(parts_query, 20)
        page_number = self.request.GET.get('page', 1)
        parts_page = paginator.get_page(page_number)
        
        # Enrich parts with AI insights
        enriched_parts = []
        for part in parts_page:
            part_data = {
                'id': part.id,
                'name': part.name,
                'description': part.description,
                'IPN': part.IPN,
                'category': part.category.name if part.category else 'Uncategorized',
                'in_stock': part.total_stock,
                'minimum_stock': part.minimum_stock,
                'has_suppliers': part.supplier_parts.exists(),
            }
            
            # Add latest forecast if available
            if hasattr(part, 'latest_forecast') and part.latest_forecast:
                forecast = part.latest_forecast[0]
                part_data['forecast'] = {
                    'predicted_demand': float(forecast.predicted_demand),
                    'confidence_lower': float(forecast.confidence_lower),
                    'confidence_upper': float(forecast.confidence_upper),
                    'trend_direction': forecast.trend_direction,
                    'forecast_horizon_days': forecast.forecast_horizon_days,
                }
                
                # Calculate days until stockout
                if forecast.predicted_demand > 0 and part.total_stock > 0:
                    days_until_stockout = int(part.total_stock / (forecast.predicted_demand / forecast.forecast_horizon_days))
                    part_data['days_until_stockout'] = days_until_stockout
                else:
                    part_data['days_until_stockout'] = None
            else:
                part_data['forecast'] = None
                part_data['days_until_stockout'] = None
            
            # Check if below reorder point
            part_data['below_reorder_point'] = part.total_stock < part.minimum_stock
            
            enriched_parts.append(part_data)
        
        context['parts'] = enriched_parts
        context['page_obj'] = parts_page
        context['search_query'] = search_query
        
        return context


class PartDetailView(LoginRequiredMixin, TemplateView):
    """Part detail view with AI insights."""
    
    template_name = 'ailms/part_detail.html'
    
    def get_context_data(self, **kwargs):
        from part.models import Part
        from company.models import SupplierPart
        from django.db.models import Prefetch
        
        context = super().get_context_data(**kwargs)
        part_id = kwargs.get('part_id')
        
        try:
            # Get part with related data
            part = Part.objects.select_related('category').prefetch_related(
                Prefetch(
                    'demand_forecasts',
                    queryset=DemandForecast.objects.order_by('-created_at')[:1],
                    to_attr='latest_forecast'
                ),
                Prefetch(
                    'supplier_parts',
                    queryset=SupplierPart.objects.select_related('supplier').prefetch_related(
                        Prefetch(
                            'supplier__evaluations',
                            queryset=SupplierEvaluation.objects.filter(part_id=part_id).order_by('-created_at')[:1],
                            to_attr='latest_evaluation'
                        )
                    )
                )
            ).get(id=part_id)
            
            context['part'] = part
            
            # Get latest forecast
            if hasattr(part, 'latest_forecast') and part.latest_forecast:
                forecast = part.latest_forecast[0]
                context['forecast'] = {
                    'predicted_demand': float(forecast.predicted_demand),
                    'confidence_lower': float(forecast.confidence_lower),
                    'confidence_upper': float(forecast.confidence_upper),
                    'trend_direction': forecast.trend_direction,
                    'forecast_horizon_days': forecast.forecast_horizon_days,
                    'model_used': forecast.model_used,
                    'seasonality_detected': forecast.seasonality_detected,
                    'created_at': forecast.created_at,
                }
                
                # Calculate days until stockout
                if forecast.predicted_demand > 0 and part.total_stock > 0:
                    days_until_stockout = int(part.total_stock / (forecast.predicted_demand / forecast.forecast_horizon_days))
                    context['days_until_stockout'] = days_until_stockout
                else:
                    context['days_until_stockout'] = None
            else:
                context['forecast'] = None
                context['days_until_stockout'] = None
            
            # Get supplier rankings
            suppliers = []
            for supplier_part in part.supplier_parts.all():
                supplier_data = {
                    'id': supplier_part.supplier.id,
                    'name': supplier_part.supplier.name,
                    'SKU': supplier_part.SKU,
                    'unit_price': supplier_part.unit_price,
                    'lead_time': supplier_part.lead_time,
                    'MOQ': supplier_part.MOQ,
                }
                
                # Add latest evaluation if available
                if hasattr(supplier_part.supplier, 'latest_evaluation') and supplier_part.supplier.latest_evaluation:
                    eval_data = supplier_part.supplier.latest_evaluation[0]
                    supplier_data['evaluation'] = {
                        'overall_score': float(eval_data.overall_score),
                        'price_score': float(eval_data.price_score),
                        'lead_time_score': float(eval_data.lead_time_score),
                        'reliability_score': float(eval_data.reliability_score),
                        'ranking_position': eval_data.ranking_position,
                        'recommendation_reason': eval_data.recommendation_reason,
                    }
                else:
                    supplier_data['evaluation'] = None
                
                suppliers.append(supplier_data)
            
            # Sort by evaluation score if available
            suppliers.sort(key=lambda s: s['evaluation']['overall_score'] if s['evaluation'] else 0, reverse=True)
            context['suppliers'] = suppliers
            
            # Get recent pipeline executions
            context['recent_pipelines'] = PipelineExecution.objects.filter(
                part_id=part_id
            ).order_by('-created_at')[:5]
            
        except Part.DoesNotExist:
            context['part'] = None
            context['forecast'] = None
            context['suppliers'] = []
            context['recent_pipelines'] = []
        
        return context


class PipelineListView(LoginRequiredMixin, TemplateView):
    """Pipeline list view."""
    
    template_name = 'ailms/pipeline_list.html'


class PipelineStatusView(LoginRequiredMixin, TemplateView):
    """Pipeline status view."""
    
    template_name = 'ailms/pipeline_status.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pipeline_id = kwargs.get('pipeline_id')
        
        try:
            pipeline = PipelineExecution.objects.select_related('part').get(id=pipeline_id)
            context['pipeline'] = pipeline
        except PipelineExecution.DoesNotExist:
            context['pipeline'] = None
        
        return context


class ApprovalQueueView(LoginRequiredMixin, TemplateView):
    """Approval queue view."""
    
    template_name = 'ailms/approval_queue.html'
    
    def get_context_data(self, **kwargs):
        from django.utils import timezone
        
        context = super().get_context_data(**kwargs)
        
        # Get filter status from query params
        filter_status = self.request.GET.get('status', 'pending')
        
        # Build query
        approvals_query = ApprovalRequest.objects.select_related(
            'part', 'pipeline', 'decision_log'
        ).filter(status=filter_status)
        
        # For pending approvals, only show non-expired ones
        if filter_status == 'pending':
            approvals_query = approvals_query.filter(expires_at__gt=timezone.now())
        
        # Order by creation time (newest first)
        approvals = approvals_query.order_by('-created_at')[:20]
        
        # Enrich approvals with data
        enriched_approvals = []
        for approval in approvals:
            state_data = approval.pipeline.state_data or {}
            
            approval_data = {
                'id': approval.id,
                'pipeline_id': approval.pipeline_id,
                'part': approval.part,
                'status': approval.status,
                'created_at': approval.created_at,
                'expires_at': approval.expires_at,
                'decision': {
                    'decision': approval.decision_log.decision,
                    'recommended_quantity': float(approval.decision_log.recommended_quantity),
                    'recommended_supplier_id': approval.decision_log.recommended_supplier_id,
                    'reasoning': approval.decision_log.reasoning,
                    'confidence_level': approval.decision_log.confidence_level,
                    'risk_factors': approval.decision_log.risk_factors,
                },
                'forecast': state_data.get('forecast', {}),
                'suppliers': state_data.get('suppliers', [])[:3],  # Top 3
            }
            
            enriched_approvals.append(approval_data)
        
        context['approvals'] = enriched_approvals
        context['filter_status'] = filter_status
        
        return context


class ApprovalDetailView(LoginRequiredMixin, TemplateView):
    """Approval detail view."""
    
    template_name = 'ailms/approval_detail.html'


class SupplierListView(LoginRequiredMixin, TemplateView):
    """Supplier list view."""
    
    template_name = 'ailms/supplier_list.html'


class SupplierDetailView(LoginRequiredMixin, TemplateView):
    """Supplier detail view."""
    
    template_name = 'ailms/supplier_detail.html'


class InventoryListView(LoginRequiredMixin, TemplateView):
    """Inventory list view."""
    
    template_name = 'ailms/inventory_list.html'


class InventoryDetailView(LoginRequiredMixin, TemplateView):
    """Inventory detail view."""
    
    template_name = 'ailms/inventory_detail.html'


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """Analytics dashboard view."""
    
    template_name = 'ailms/analytics.html'
