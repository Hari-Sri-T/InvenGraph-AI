"""Approval Gate: Handles human-in-the-loop approval workflow."""

from datetime import datetime, timedelta
from typing import Dict

from part.models import Part

from .models import ApprovalRequest, PipelineExecution, ProcurementDecisionLog
from .notifications import NotificationService


class ApprovalGate:
    """Manages human approval workflow for procurement decisions."""

    APPROVAL_TIMEOUT_DAYS = 7

    def __init__(self):
        """Initialize Approval Gate."""
        self.notification_service = NotificationService()

    def create_approval_request(
        self, pipeline_id: str, decision: Dict
    ) -> ApprovalRequest:
        """
        Create an approval request for a procurement decision.

        Args:
            pipeline_id: UUID of the pipeline execution
            decision: Procurement decision dictionary

        Returns:
            Created ApprovalRequest instance
        """
        try:
            # Get pipeline execution
            pipeline = PipelineExecution.objects.get(id=pipeline_id)

            # Create decision log
            decision_log = ProcurementDecisionLog.objects.create(
                pipeline=pipeline,
                part_id=pipeline.part_id,
                decision=decision['decision'],
                recommended_quantity=decision['recommended_quantity'],
                recommended_supplier_id=decision.get('recommended_supplier_id'),
                reasoning=decision['reasoning'],
                confidence_level=decision.get('confidence_level', 'medium'),
                risk_factors=decision.get('risk_factors', []),
                alternative_actions=decision.get('alternative_actions', []),
                llm_model_used=decision.get('llm_model_used', ''),
                llm_response_time_ms=decision.get('llm_response_time_ms', 0),
            )

            # Create approval request
            expires_at = datetime.now() + timedelta(days=self.APPROVAL_TIMEOUT_DAYS)

            approval_request = ApprovalRequest.objects.create(
                pipeline=pipeline,
                part_id=pipeline.part_id,
                decision_log=decision_log,
                status='pending',
                expires_at=expires_at,
            )

            print(
                f'Created approval request {approval_request.id} for pipeline {pipeline_id}'
            )

            return approval_request

        except Exception as e:
            print(f'Error creating approval request: {e}')
            raise

    def send_notifications(self, approval_request: ApprovalRequest):
        """
        Send notifications for approval request.

        Args:
            approval_request: ApprovalRequest instance
        """
        try:
            # Send in-app notification
            self.notification_service.send_in_app_notification(approval_request)

            # Send email notification
            self.notification_service.send_email_notification(approval_request)

        except Exception as e:
            print(f'Error sending notifications: {e}')
            # Don't raise - notification failure shouldn't block pipeline

    def process_approval(
        self, request_id: str, user_id: int, action: str, user_data: Dict
    ) -> Dict:
        """
        Process approval response from user.

        Args:
            request_id: UUID of the approval request
            user_id: ID of the user responding
            action: User action ('approve', 'reject', 'modify')
            user_data: Additional user data (modified_quantity, modified_supplier_id, notes)

        Returns:
            Dictionary with resume data for pipeline
        """
        try:
            # Get approval request
            approval_request = ApprovalRequest.objects.get(id=request_id)

            # Validate status
            if approval_request.status != 'pending':
                raise Exception(
                    f'Approval request already processed: {approval_request.status}'
                )

            # Check expiration
            if datetime.now() > approval_request.expires_at:
                approval_request.status = 'expired'
                approval_request.save()
                raise Exception('Approval request has expired')

            # Update approval request
            approval_request.status = action
            approval_request.action = action
            approval_request.responded_at = datetime.now()
            approval_request.responded_by_id = user_id
            approval_request.modified_quantity = user_data.get('modified_quantity')
            approval_request.modified_supplier_id = user_data.get('modified_supplier_id')
            approval_request.user_notes = user_data.get('user_notes', '')
            approval_request.save()

            print(
                f'Approval request {request_id} processed: {action} by user {user_id}'
            )

            # Prepare resume data
            resume_data = {
                'action': action,
                'modified_quantity': user_data.get('modified_quantity'),
                'modified_supplier_id': user_data.get('modified_supplier_id'),
                'user_notes': user_data.get('user_notes', ''),
                'request_id': str(request_id),
            }

            return resume_data

        except ApprovalRequest.DoesNotExist:
            raise Exception(f'Approval request {request_id} not found')
        except Exception as e:
            print(f'Error processing approval: {e}')
            raise

    def resume_pipeline_after_approval(
        self, request_id: str, user_id: int, action: str, user_data: Dict
    ) -> str:
        """
        Resume pipeline execution after approval.

        Args:
            request_id: UUID of the approval request
            user_id: ID of the user responding
            action: User action ('approve', 'reject', 'modify')
            user_data: Additional user data

        Returns:
            Pipeline ID
        """
        try:
            # Process approval
            resume_data = self.process_approval(request_id, user_id, action, user_data)

            # Get approval request and pipeline
            approval_request = ApprovalRequest.objects.get(id=request_id)
            pipeline_id = str(approval_request.pipeline.id)

            # Resume pipeline with human decision
            from .graph import compile_procurement_graph
            from .state_manager import StateManager

            state_manager = StateManager()

            # Load current state
            state = state_manager.load_checkpoint(pipeline_id)
            if not state:
                raise Exception(f'Pipeline state not found for {pipeline_id}')

            # Update state with human decision
            state['human_decision'] = resume_data
            state['status'] = 'running'

            # If rejected, mark as complete
            if action == 'reject':
                state_manager.mark_pipeline_rejected(
                    pipeline_id, 'Rejected by user'
                )
                return pipeline_id

            # Resume graph execution
            graph = compile_procurement_graph()
            config = {'configurable': {'thread_id': pipeline_id}}

            # Continue from where we left off
            result = graph.invoke(state, config)

            print(f'Pipeline {pipeline_id} resumed after approval')

            return pipeline_id

        except Exception as e:
            print(f'Error resuming pipeline: {e}')
            raise
