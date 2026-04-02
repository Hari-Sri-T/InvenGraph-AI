"""Views for AI-First Logistics Management System Web Interface."""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.views.generic import TemplateView
from django.utils import timezone
from django.urls import reverse_lazy
from django.db.models import Avg, Count, Q, F, Sum
from datetime import timedelta

from ai_procurement.models import (
    PipelineExecution,
    ApprovalRequest,
    ProcurementDecisionLog,
    DemandForecast,
    SupplierEvaluation,
)


class AILoginView(DjangoLoginView):
    """Simple login view for AI interface."""
    
    template_name = 'ailms/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """Redirect to the 'next' parameter or dashboard after login."""
        next_url = self.request.GET.get('next')
        if next_url:
            return next_url
        return reverse_lazy('ailms:dashboard')


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
                # Get unit pricing from price breaks
                unit_price = supplier_part.unit_pricing if hasattr(supplier_part, 'unit_pricing') else None
                
                supplier_data = {
                    'id': supplier_part.supplier.id,
                    'name': supplier_part.supplier.name,
                    'SKU': supplier_part.SKU,
                    'unit_price': unit_price,
                    'pack_quantity': supplier_part.pack_quantity,
                    'multiple': supplier_part.multiple,
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
    """Supplier list view with AI scoring."""
    
    template_name = 'ailms/supplier_list.html'
    
    def get_context_data(self, **kwargs):
        from company.models import Company
        from ai_procurement.models import SupplierReliabilityScore, SupplierEvaluation
        from django.db.models import Prefetch, Avg, Q
        
        context = super().get_context_data(**kwargs)
        
        # Get search query
        search_query = self.request.GET.get('search', '')
        
        # Build suppliers query (only active suppliers)
        suppliers_query = Company.objects.filter(
            is_supplier=True,
            active=True
        )
        
        if search_query:
            suppliers_query = suppliers_query.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Prefetch reliability scores
        suppliers_query = suppliers_query.prefetch_related(
            Prefetch(
                'reliability_scores',
                queryset=SupplierReliabilityScore.objects.filter(part__isnull=True).order_by('-last_updated')[:1],
                to_attr='latest_reliability_score'
            )
        )
        
        # Get all suppliers
        suppliers = list(suppliers_query)
        
        # Enrich suppliers with AI scores
        enriched_suppliers = []
        for supplier in suppliers:
            supplier_data = {
                'id': supplier.id,
                'name': supplier.name,
                'description': supplier.description,
                'active': supplier.active,
                'website': supplier.website,
                'email': supplier.email,
                'phone': supplier.phone,
            }
            
            # Add reliability metrics if available
            if hasattr(supplier, 'latest_reliability_score') and supplier.latest_reliability_score:
                score = supplier.latest_reliability_score[0]
                supplier_data['reliability_metrics'] = {
                    'on_time_delivery_rate': float(score.on_time_delivery_rate),
                    'quality_acceptance_rate': float(score.quality_acceptance_rate),
                    'lead_time_accuracy': float(score.lead_time_accuracy),
                    'total_orders': score.total_orders,
                    'successful_orders': score.successful_orders,
                }
            else:
                supplier_data['reliability_metrics'] = None
            
            # Calculate average AI scores from recent evaluations
            recent_evaluations = SupplierEvaluation.objects.filter(
                supplier=supplier
            ).order_by('-created_at')[:10]
            
            if recent_evaluations.exists():
                avg_scores = recent_evaluations.aggregate(
                    overall=Avg('overall_score'),
                    price=Avg('price_score'),
                    lead_time=Avg('lead_time_score'),
                    reliability=Avg('reliability_score')
                )
                supplier_data['ai_scores'] = {
                    'overall_score': float(avg_scores['overall'] or 0),
                    'price_score': float(avg_scores['price'] or 0),
                    'lead_time_score': float(avg_scores['lead_time'] or 0),
                    'reliability_score': float(avg_scores['reliability'] or 0),
                }
            else:
                supplier_data['ai_scores'] = None
            
            enriched_suppliers.append(supplier_data)
        
        # Sort by AI overall score (descending)
        enriched_suppliers.sort(
            key=lambda s: s['ai_scores']['overall_score'] if s['ai_scores'] else 0,
            reverse=True
        )
        
        context['suppliers'] = enriched_suppliers
        context['search_query'] = search_query
        
        return context


class SupplierDetailView(LoginRequiredMixin, TemplateView):
    """Supplier detail view with AI scores and parts."""
    
    template_name = 'ailms/supplier_detail.html'
    
    def get_context_data(self, **kwargs):
        from company.models import Company, SupplierPart
        from ai_procurement.models import SupplierReliabilityScore, SupplierEvaluation
        from django.db.models import Prefetch, Avg
        
        context = super().get_context_data(**kwargs)
        supplier_id = kwargs.get('pk')
        
        try:
            # Get supplier with related data
            supplier = Company.objects.prefetch_related(
                Prefetch(
                    'reliability_scores',
                    queryset=SupplierReliabilityScore.objects.filter(part__isnull=True).order_by('-last_updated')[:1],
                    to_attr='latest_reliability_score'
                )
            ).get(id=supplier_id, is_supplier=True)
            
            context['supplier'] = supplier
            
            # Get reliability metrics
            if hasattr(supplier, 'latest_reliability_score') and supplier.latest_reliability_score:
                score = supplier.latest_reliability_score[0]
                context['reliability_metrics'] = {
                    'on_time_delivery_rate': float(score.on_time_delivery_rate),
                    'quality_acceptance_rate': float(score.quality_acceptance_rate),
                    'lead_time_accuracy': float(score.lead_time_accuracy),
                    'total_orders': score.total_orders,
                    'successful_orders': score.successful_orders,
                    'last_updated': score.last_updated,
                }
            else:
                context['reliability_metrics'] = None
            
            # Calculate average AI scores from recent evaluations
            recent_evaluations = SupplierEvaluation.objects.filter(
                supplier=supplier
            ).order_by('-created_at')[:10]
            
            if recent_evaluations.exists():
                avg_scores = recent_evaluations.aggregate(
                    overall=Avg('overall_score'),
                    price=Avg('price_score'),
                    lead_time=Avg('lead_time_score'),
                    reliability=Avg('reliability_score')
                )
                context['ai_scores'] = {
                    'overall_score': float(avg_scores['overall'] or 0),
                    'price_score': float(avg_scores['price'] or 0),
                    'lead_time_score': float(avg_scores['lead_time'] or 0),
                    'reliability_score': float(avg_scores['reliability'] or 0),
                }
            else:
                context['ai_scores'] = None
            
            # Get all parts supplied by this supplier
            supplier_parts = SupplierPart.objects.filter(
                supplier=supplier
            ).select_related('part').order_by('part__name')
            
            parts_data = []
            for sp in supplier_parts:
                # Get unit pricing from price breaks
                unit_price = sp.unit_pricing if hasattr(sp, 'unit_pricing') else None
                
                parts_data.append({
                    'part_id': sp.part.id,
                    'part_name': sp.part.name,
                    'part_IPN': sp.part.IPN,
                    'SKU': sp.SKU,
                    'unit_price': unit_price,
                    'multiple': sp.multiple,
                    'pack_quantity': sp.pack_quantity,
                })
            
            context['parts'] = parts_data
            
        except Company.DoesNotExist:
            context['supplier'] = None
            context['reliability_metrics'] = None
            context['ai_scores'] = None
            context['parts'] = []
        
        return context


class InventoryListView(LoginRequiredMixin, TemplateView):
    """Inventory list view with AI optimization recommendations."""
    
    template_name = 'ailms/inventory_list.html'
    
    def get_context_data(self, **kwargs):
        from part.models import Part
        from stock.models import StockItem, StockLocation
        from django.db.models import Q, Sum, Prefetch
        
        context = super().get_context_data(**kwargs)
        
        # Get search query and filter
        search_query = self.request.GET.get('search', '')
        alert_filter = self.request.GET.get('alert', '')  # 'low_stock', 'stockout_risk', or ''
        
        # Build parts query
        parts_query = Part.objects.filter(active=True).select_related('category')
        
        if search_query:
            parts_query = parts_query.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(IPN__icontains=search_query)
            )
        
        # Prefetch stock items and latest forecast
        parts_query = parts_query.prefetch_related(
            Prefetch(
                'stock_items',
                queryset=StockItem.objects.select_related('location').filter(quantity__gt=0)
            ),
            Prefetch(
                'demand_forecasts',
                queryset=DemandForecast.objects.order_by('-created_at')[:1],
                to_attr='latest_forecast'
            )
        )
        
        # Get all parts
        parts = list(parts_query)
        
        # Enrich parts with inventory and AI data
        enriched_parts = []
        for part in parts:
            # Calculate total stock across all locations
            total_stock = part.total_stock
            
            # Get stock by location
            stock_by_location = []
            for stock_item in part.stock_items.all():
                stock_by_location.append({
                    'location': stock_item.location.name if stock_item.location else 'No Location',
                    'quantity': float(stock_item.quantity),
                })
            
            part_data = {
                'id': part.id,
                'name': part.name,
                'description': part.description,
                'IPN': part.IPN,
                'category': part.category.name if part.category else 'Uncategorized',
                'total_stock': total_stock,
                'minimum_stock': part.minimum_stock,
                'stock_by_location': stock_by_location,
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
                    'forecast_accuracy_score': float(forecast.forecast_accuracy_score) if forecast.forecast_accuracy_score else None,
                }
                
                # Calculate days until stockout
                if forecast.predicted_demand > 0 and total_stock > 0:
                    daily_demand = forecast.predicted_demand / forecast.forecast_horizon_days
                    days_until_stockout = int(total_stock / daily_demand)
                    part_data['days_until_stockout'] = days_until_stockout
                    
                    # Determine stockout risk level
                    if days_until_stockout <= 7:
                        part_data['stockout_risk'] = 'high'
                    elif days_until_stockout <= 14:
                        part_data['stockout_risk'] = 'medium'
                    else:
                        part_data['stockout_risk'] = 'low'
                else:
                    part_data['days_until_stockout'] = None
                    part_data['stockout_risk'] = 'unknown'
            else:
                part_data['forecast'] = None
                part_data['days_until_stockout'] = None
                part_data['stockout_risk'] = 'unknown'
            
            # Check if below minimum stock
            part_data['below_minimum'] = total_stock < part.minimum_stock
            
            # Generate alerts
            alerts = []
            if part_data['below_minimum']:
                alerts.append({
                    'type': 'low_stock',
                    'severity': 'warning',
                    'message': f'Stock level ({total_stock}) below minimum ({part.minimum_stock})'
                })
            
            if part_data['stockout_risk'] == 'high':
                alerts.append({
                    'type': 'stockout_risk',
                    'severity': 'error',
                    'message': f'High stockout risk: {part_data["days_until_stockout"]} days until stockout'
                })
            elif part_data['stockout_risk'] == 'medium':
                alerts.append({
                    'type': 'stockout_risk',
                    'severity': 'warning',
                    'message': f'Medium stockout risk: {part_data["days_until_stockout"]} days until stockout'
                })
            
            part_data['alerts'] = alerts
            
            # Apply alert filter
            if alert_filter == 'low_stock' and not part_data['below_minimum']:
                continue
            if alert_filter == 'stockout_risk' and part_data['stockout_risk'] not in ['high', 'medium']:
                continue
            
            enriched_parts.append(part_data)
        
        # Sort by stockout risk (high risk first)
        risk_order = {'high': 0, 'medium': 1, 'low': 2, 'unknown': 3}
        enriched_parts.sort(key=lambda p: (risk_order.get(p['stockout_risk'], 3), -p['total_stock']))
        
        context['parts'] = enriched_parts
        context['search_query'] = search_query
        context['alert_filter'] = alert_filter
        
        # Calculate summary stats
        context['total_parts'] = len(enriched_parts)
        context['low_stock_count'] = sum(1 for p in enriched_parts if p['below_minimum'])
        context['high_risk_count'] = sum(1 for p in enriched_parts if p['stockout_risk'] == 'high')
        
        return context


class InventoryDetailView(LoginRequiredMixin, TemplateView):
    """Inventory detail view."""
    
    template_name = 'ailms/inventory_detail.html'


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    """Analytics dashboard view with AI performance metrics."""
    
    template_name = 'ailms/analytics.html'
    
    def get_context_data(self, **kwargs):
        from django.db.models import Avg, Count, Q, F
        from django.utils import timezone
        from datetime import timedelta
        from part.models import PartCategory
        
        context = super().get_context_data(**kwargs)
        
        # Time range for analytics (last 30 days)
        start_date = timezone.now() - timedelta(days=30)
        
        # 1. Forecast Accuracy Metrics
        recent_forecasts = DemandForecast.objects.filter(
            created_at__gte=start_date,
            forecast_accuracy_score__isnull=False
        )
        
        if recent_forecasts.exists():
            avg_accuracy = recent_forecasts.aggregate(avg=Avg('forecast_accuracy_score'))['avg']
            context['forecast_accuracy'] = float(avg_accuracy or 0) * 100
            
            # Forecast accuracy by category
            accuracy_by_category = []
            categories = PartCategory.objects.all()
            for category in categories:
                cat_forecasts = recent_forecasts.filter(part__category=category)
                if cat_forecasts.exists():
                    cat_avg = cat_forecasts.aggregate(avg=Avg('forecast_accuracy_score'))['avg']
                    accuracy_by_category.append({
                        'category': category.name,
                        'accuracy': float(cat_avg or 0) * 100,
                        'count': cat_forecasts.count()
                    })
            
            context['accuracy_by_category'] = accuracy_by_category
        else:
            context['forecast_accuracy'] = 0
            context['accuracy_by_category'] = []
        
        # 2. Procurement Metrics
        recent_pipelines = PipelineExecution.objects.filter(created_at__gte=start_date)
        total_pipelines = recent_pipelines.count()
        
        if total_pipelines > 0:
            completed_pipelines = recent_pipelines.filter(status='completed').count()
            success_rate = (completed_pipelines / total_pipelines) * 100
            
            # Calculate average execution time for completed pipelines
            completed = recent_pipelines.filter(status='completed', completed_at__isnull=False)
            if completed.exists():
                total_time = sum(
                    [(p.completed_at - p.created_at).total_seconds() for p in completed],
                    0
                )
                avg_execution_time = total_time / completed.count()
            else:
                avg_execution_time = 0
            
            context['procurement_metrics'] = {
                'total_pipelines': total_pipelines,
                'completed': completed_pipelines,
                'success_rate': success_rate,
                'avg_execution_time': avg_execution_time,
                'interrupted': recent_pipelines.filter(status='interrupted').count(),
                'failed': recent_pipelines.filter(status='failed').count(),
            }
        else:
            context['procurement_metrics'] = {
                'total_pipelines': 0,
                'completed': 0,
                'success_rate': 0,
                'avg_execution_time': 0,
                'interrupted': 0,
                'failed': 0,
            }
        
        # 3. Supplier Performance
        from ai_procurement.models import SupplierReliabilityScore
        from company.models import Company
        
        suppliers = Company.objects.filter(is_supplier=True, active=True)
        supplier_performance = []
        
        for supplier in suppliers:
            # Get average reliability scores
            reliability_scores = SupplierReliabilityScore.objects.filter(
                supplier=supplier,
                last_updated__gte=start_date
            )
            
            if reliability_scores.exists():
                avg_scores = reliability_scores.aggregate(
                    on_time=Avg('on_time_delivery_rate'),
                    quality=Avg('quality_acceptance_rate'),
                    lead_time=Avg('lead_time_accuracy')
                )
                
                # Get average AI evaluation scores
                recent_evaluations = SupplierEvaluation.objects.filter(
                    supplier=supplier,
                    created_at__gte=start_date
                )
                
                if recent_evaluations.exists():
                    ai_avg = recent_evaluations.aggregate(avg=Avg('overall_score'))['avg']
                    ai_score = float(ai_avg or 0)
                else:
                    ai_score = 0
                
                supplier_performance.append({
                    'name': supplier.name,
                    'on_time_delivery': float(avg_scores['on_time'] or 0) * 100,
                    'quality_acceptance': float(avg_scores['quality'] or 0) * 100,
                    'lead_time_accuracy': float(avg_scores['lead_time'] or 0) * 100,
                    'ai_score': ai_score,
                })
        
        # Sort by AI score descending
        supplier_performance.sort(key=lambda s: s['ai_score'], reverse=True)
        context['supplier_performance'] = supplier_performance[:10]  # Top 10
        
        # 4. Demand Trends (for Chart.js)
        # Get historical demand data (last 30 days)
        demand_trends = []
        for i in range(30, -1, -1):
            date = (timezone.now() - timedelta(days=i)).date()
            
            # Get forecasts created on this date
            forecasts_on_date = DemandForecast.objects.filter(
                created_at__date=date
            )
            
            if forecasts_on_date.exists():
                total_demand = forecasts_on_date.aggregate(total=Sum('predicted_demand'))['total']
                demand_trends.append({
                    'date': date.isoformat(),
                    'demand': float(total_demand or 0)
                })
            else:
                demand_trends.append({
                    'date': date.isoformat(),
                    'demand': 0
                })
        
        context['demand_trends'] = demand_trends
        
        return context
