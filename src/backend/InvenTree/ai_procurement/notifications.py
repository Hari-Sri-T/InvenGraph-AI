"""Notification Service: Delivers approval requests via in-app and email."""

from typing import List

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.urls import reverse

from part.models import Part

from .models import ApprovalRequest


class NotificationService:
    """Handles notification delivery for approval requests."""

    def __init__(self):
        """Initialize Notification Service."""
        pass

    def get_responsible_users(self, part_id: int) -> List[User]:
        """
        Get list of users responsible for approving procurement for a part.

        Args:
            part_id: ID of the part

        Returns:
            List of User instances
        """
        try:
            part = Part.objects.get(pk=part_id)

            # Get responsible owner if set
            if part.responsible:
                return [part.responsible]

            # Fallback: Get all users with purchase_order.add permission
            users = User.objects.filter(
                is_active=True, user_permissions__codename='add_purchaseorder'
            )

            if users.exists():
                return list(users)

            # Last resort: Get all superusers
            return list(User.objects.filter(is_active=True, is_superuser=True))

        except Part.DoesNotExist:
            return []
        except Exception as e:
            print(f'Error getting responsible users: {e}')
            return []

    def format_notification_message(
        self, approval_request: ApprovalRequest
    ) -> tuple[str, str]:
        """
        Format notification message for approval request.

        Args:
            approval_request: ApprovalRequest instance

        Returns:
            Tuple of (title, message)
        """
        try:
            part = approval_request.part
            decision_log = approval_request.decision_log
            pipeline = approval_request.pipeline

            # Get forecast and supplier data from pipeline state
            state_data = pipeline.state_data or {}
            forecast = state_data.get('forecast', {})
            suppliers = state_data.get('suppliers', [])

            # Find recommended supplier
            recommended_supplier = None
            if decision_log.recommended_supplier_id:
                for supplier in suppliers:
                    if supplier.get('supplier_id') == decision_log.recommended_supplier_id:
                        recommended_supplier = supplier
                        break

            title = f'Procurement Approval Required: {part.name}'

            message = f"""
A procurement decision requires your approval:

Part: {part.name}
Current Stock: {state_data.get('data_collection', {}).get('current_stock', 'N/A')} units
Minimum Stock: {state_data.get('data_collection', {}).get('minimum_stock', 'N/A')} units

Forecast (30 days):
- Predicted Demand: {forecast.get('predicted_demand', 'N/A')} units
- Confidence: [{forecast.get('confidence_lower', 'N/A')}, {forecast.get('confidence_upper', 'N/A')}]
- Trend: {forecast.get('trend_direction', 'N/A')}

Recommendation:
- Decision: {decision_log.decision}
- Quantity: {decision_log.recommended_quantity} units
- Supplier: {recommended_supplier['supplier_name'] if recommended_supplier else 'N/A'}
- Unit Price: ${recommended_supplier['unit_price'] if recommended_supplier else 'N/A'}
- Lead Time: {recommended_supplier['estimated_delivery_days'] if recommended_supplier else 'N/A'} days

AI Reasoning:
{decision_log.reasoning}

Confidence Level: {decision_log.confidence_level}

Please review and approve/reject this procurement decision.
"""

            return title, message

        except Exception as e:
            print(f'Error formatting notification message: {e}')
            return 'Procurement Approval Required', 'Please review the procurement decision.'

    def send_in_app_notification(self, approval_request: ApprovalRequest):
        """
        Send in-app notification to responsible users.

        Args:
            approval_request: ApprovalRequest instance
        """
        try:
            # Get responsible users
            users = self.get_responsible_users(approval_request.part_id)

            if not users:
                print('No responsible users found for in-app notification')
                return

            # Format message
            title, message = self.format_notification_message(approval_request)

            # Create notification for each user
            # Note: InvenTree's notification system would be used here
            # For now, we'll just log it
            for user in users:
                print(f'In-app notification sent to {user.username}: {title}')

            # TODO: Integrate with InvenTree's notification system
            # from InvenTree.notifications import NotificationEntry
            # NotificationEntry.notify(...)

        except Exception as e:
            print(f'Error sending in-app notification: {e}')

    def send_email_notification(self, approval_request: ApprovalRequest):
        """
        Send email notification to responsible users.

        Args:
            approval_request: ApprovalRequest instance
        """
        try:
            # Get responsible users
            users = self.get_responsible_users(approval_request.part_id)

            if not users:
                print('No responsible users found for email notification')
                return

            # Format message
            title, message = self.format_notification_message(approval_request)

            # Get approval URL
            # TODO: Generate proper approval URL with signed token
            approval_url = f'{settings.SITE_URL}/ai-procurement/approval/{approval_request.id}/'

            # Add URL to message
            email_message = message + f'\n\nApprove here: {approval_url}'

            # Send email to each user
            recipient_emails = [user.email for user in users if user.email]

            if recipient_emails:
                send_mail(
                    subject=title,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=recipient_emails,
                    fail_silently=True,  # Don't raise exception on email failure
                )

                print(f'Email notification sent to {len(recipient_emails)} users')
            else:
                print('No email addresses found for users')

        except Exception as e:
            print(f'Error sending email notification: {e}')
