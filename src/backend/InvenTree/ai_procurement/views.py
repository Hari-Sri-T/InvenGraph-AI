"""API views for Agentic AI Procurement System."""

import warnings

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from company.models import SupplierPart
from order.models import PurchaseOrder, PurchaseOrderLineItem
from part.models import Part

from .approval_gate import ApprovalGate
from .models import ApprovalRequest, PipelineExecution
from .signals import trigger_pipeline_async


# ==========================================
# LEGACY ENDPOINTS (Backward Compatibility)
# ==========================================


class ProcurementRunView(APIView):
    """
    DEPRECATED: Legacy endpoint for manual pipeline triggering.
    Use PipelineTriggerView instead.

    POST /api/ai/procurement/run/
    Expects JSON: {"part_id": <int>}
    """

    def post(self, request):
        warnings.warn(
            'ProcurementRunView is deprecated. Use PipelineTriggerView instead.',
            DeprecationWarning,
        )

        part_id = request.data.get('part_id')
        if not part_id:
            return Response(
                {'error': 'part_id is required'}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate part exists
        try:
            part = Part.objects.get(pk=part_id)
        except Part.DoesNotExist:
            return Response(
                {'error': f'Part {part_id} not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Trigger the new pipeline system
        trigger_reason = 'Legacy API trigger'
        pipeline_id = trigger_pipeline_async(part_id, trigger_reason)

        if pipeline_id:
            return Response(
                {
                    'pipeline_id': pipeline_id,
                    'status': 'running',
                    'message': 'Pipeline started (use new API endpoints for better control)',
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {'error': 'Failed to start pipeline'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProcurementApproveView(APIView):
    """
    DEPRECATED: Legacy endpoint for manual approval.
    Use ApprovalActionView instead.

    POST /api/ai/procurement/approve/
    Expects JSON: {"part_id": <int>, "quantity": <int>}
    """

    def post(self, request):
        warnings.warn(
            'ProcurementApproveView is deprecated. Use ApprovalActionView instead.',
            DeprecationWarning,
        )

        part_id = request.data.get('part_id')
        quantity = request.data.get('quantity')

        if not part_id or not quantity:
            return Response(
                {'error': 'part_id and quantity are required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        part = get_object_or_404(Part, pk=part_id)

        # For MVP: Grab the first supplier linked to this part
        supplier_part = SupplierPart.objects.filter(part=part).first()

        if not supplier_part:
            return Response(
                {
                    'error': f"No supplier linked to part '{part.name}'. Cannot create PO automatically."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create Draft Purchase Order (Status 10 = Pending/Draft)
        po = PurchaseOrder.objects.create(
            supplier=supplier_part.supplier,
            description=f'AI Automated Procurement for {part.name}',
            status=10,
        )

        # Add Line Item to the PO
        PurchaseOrderLineItem.objects.create(
            order=po, part=supplier_part, quantity=quantity
        )

        return Response(
            {
                'message': 'Draft Purchase Order created successfully',
                'po_id': po.id,
                'supplier': supplier_part.supplier.name,
            },
            status=status.HTTP_201_CREATED,
        )


# ==========================================
# NEW AGENTIC ENDPOINTS
# ==========================================


class PipelineTriggerView(APIView):
    """
    Manually trigger procurement pipeline for a part.

    POST /api/ai/procurement/pipeline/trigger/
    Expects JSON: {"part_id": <int>}

    Returns:
        {
            "pipeline_id": "<uuid>",
            "status": "running",
            "message": "Pipeline started successfully"
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        part_id = request.data.get('part_id')

        if not part_id:
            return Response(
                {'error': 'part_id is required'}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate part exists
        try:
            part = Part.objects.get(pk=part_id)
        except Part.DoesNotExist:
            return Response(
                {'error': f'Part {part_id} not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Trigger pipeline
        trigger_reason = f'Manual trigger by user {request.user.username}'
        pipeline_id = trigger_pipeline_async(part_id, trigger_reason)

        if pipeline_id:
            return Response(
                {
                    'pipeline_id': pipeline_id,
                    'status': 'running',
                    'message': f'Pipeline started successfully for {part.name}',
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {'error': 'Failed to start pipeline'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PipelineStatusView(APIView):
    """
    Get current pipeline status.

    GET /api/ai/procurement/pipeline/status/<pipeline_id>/
    or
    GET /api/ai/procurement/pipeline/status/?part_id=<int>

    Returns:
        {
            "pipeline_id": "<uuid>",
            "part_id": <int>,
            "status": "running|interrupted|completed|failed|rejected",
            "current_node": "<node_name>",
            "trigger_reason": "<reason>",
            "created_at": "<timestamp>",
            "updated_at": "<timestamp>",
            "completed_at": "<timestamp>",
            "error_message": "<error>"
        }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pipeline_id=None):
        # Lazy import to avoid database access during migration
        from .state_manager import StateManager

        if pipeline_id:
            # Get specific pipeline
            state_manager = StateManager()
            pipeline_status = state_manager.get_pipeline_status(pipeline_id)

            if pipeline_status:
                return Response(pipeline_status, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': f'Pipeline {pipeline_id} not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Get pipelines by part_id
            part_id = request.query_params.get('part_id')

            if not part_id:
                return Response(
                    {'error': 'pipeline_id or part_id is required'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            pipelines = PipelineExecution.objects.filter(part_id=part_id).order_by(
                '-created_at'
            )[:10]

            pipeline_list = [
                {
                    'pipeline_id': str(p.id),
                    'part_id': p.part_id,
                    'status': p.status,
                    'current_node': p.current_node,
                    'trigger_reason': p.trigger_reason,
                    'created_at': p.created_at.isoformat(),
                    'updated_at': p.updated_at.isoformat(),
                    'completed_at': (
                        p.completed_at.isoformat() if p.completed_at else None
                    ),
                }
                for p in pipelines
            ]

            return Response({'pipelines': pipeline_list}, status=status.HTTP_200_OK)


class ApprovalRequestListView(APIView):
    """
    Get pending approval requests.

    GET /api/ai/procurement/approvals/
    Optional query params:
        - part_id: Filter by part
        - status: Filter by status (pending, approved, rejected, etc.)

    Returns:
        {
            "approvals": [
                {
                    "request_id": "<uuid>",
                    "pipeline_id": "<uuid>",
                    "part_id": <int>,
                    "part_name": "<name>",
                    "status": "pending",
                    "decision": {...},
                    "forecast": {...},
                    "suppliers": [...],
                    "created_at": "<timestamp>",
                    "expires_at": "<timestamp>"
                }
            ]
        }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Get query parameters
        part_id = request.query_params.get('part_id')
        approval_status = request.query_params.get('status', 'pending')

        # Build query
        query = ApprovalRequest.objects.select_related(
            'part', 'pipeline', 'decision_log'
        ).filter(status=approval_status)

        if part_id:
            query = query.filter(part_id=part_id)

        # Get approvals
        approvals = query.order_by('-created_at')[:20]

        approval_list = []
        for approval in approvals:
            # Get pipeline state data
            state_data = approval.pipeline.state_data or {}

            approval_data = {
                'request_id': str(approval.id),
                'pipeline_id': str(approval.pipeline_id),
                'part_id': approval.part_id,
                'part_name': approval.part.name,
                'status': approval.status,
                'decision': {
                    'decision': approval.decision_log.decision,
                    'recommended_quantity': float(
                        approval.decision_log.recommended_quantity
                    ),
                    'recommended_supplier_id': approval.decision_log.recommended_supplier_id,
                    'reasoning': approval.decision_log.reasoning,
                    'confidence_level': approval.decision_log.confidence_level,
                    'risk_factors': approval.decision_log.risk_factors,
                },
                'forecast': state_data.get('forecast', {}),
                'suppliers': state_data.get('suppliers', [])[:3],  # Top 3
                'created_at': approval.created_at.isoformat(),
                'expires_at': approval.expires_at.isoformat(),
            }

            approval_list.append(approval_data)

        return Response({'approvals': approval_list}, status=status.HTTP_200_OK)


class ApprovalActionView(APIView):
    """
    Process approval action (approve/reject/modify).

    POST /api/ai/procurement/approvals/<request_id>/action/
    Expects JSON:
        {
            "action": "approve|reject|modify",
            "modified_quantity": <int> (optional, for modify),
            "modified_supplier_id": <int> (optional, for modify),
            "user_notes": "<string>" (optional)
        }

    Returns:
        {
            "message": "Approval processed successfully",
            "pipeline_id": "<uuid>",
            "status": "running|rejected"
        }
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):
        # Validate action
        action = request.data.get('action')
        if action not in ['approve', 'reject', 'modify']:
            return Response(
                {'error': 'action must be approve, reject, or modify'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check user permissions
        if not request.user.has_perm('order.add_purchaseorder'):
            return Response(
                {'error': 'User does not have permission to approve purchase orders'},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            # Process approval
            approval_gate = ApprovalGate()
            user_data = {
                'modified_quantity': request.data.get('modified_quantity'),
                'modified_supplier_id': request.data.get('modified_supplier_id'),
                'user_notes': request.data.get('user_notes', ''),
            }

            resume_data = approval_gate.process_approval(
                request_id, request.user.id, action, user_data
            )

            # Resume pipeline
            approval_request = ApprovalRequest.objects.get(id=request_id)
            
            # Lazy import to avoid database access during migration
            from .state_manager import StateManager
            
            state_manager = StateManager()
            updated_state = state_manager.resume_pipeline(
                str(approval_request.pipeline_id), resume_data
            )

            if updated_state:
                # Continue pipeline execution
                from .graph import compile_procurement_graph

                graph = compile_procurement_graph()
                config = {'configurable': {'thread_id': str(approval_request.pipeline_id)}}

                # Resume from execution node
                result = graph.invoke(updated_state, config)

                return Response(
                    {
                        'message': 'Approval processed successfully',
                        'pipeline_id': str(approval_request.pipeline_id),
                        'status': result.get('status', 'running'),
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {'error': 'Failed to resume pipeline'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

        except ApprovalRequest.DoesNotExist:
            return Response(
                {'error': f'Approval request {request_id} not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to process approval: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )