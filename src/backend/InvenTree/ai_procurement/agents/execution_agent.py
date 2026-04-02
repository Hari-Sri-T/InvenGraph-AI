"""Execution Agent: Creates PurchaseOrders in InvenTree after approval."""

from decimal import Decimal
from typing import Optional

from django.db import transaction

from company.models import Company, SupplierPart
from order.models import PurchaseOrder, PurchaseOrderLineItem
from part.models import Part


class ExecutionAgent:
    """Agent responsible for creating PurchaseOrders."""

    def __init__(self):
        """Initialize Execution Agent."""
        pass

    def validate_po_data(
        self, part_id: int, supplier_id: int, quantity: float
    ) -> tuple[bool, str]:
        """
        Validate purchase order data before creation.

        Args:
            part_id: ID of the part
            supplier_id: ID of the supplier
            quantity: Quantity to order

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate part exists
            part = Part.objects.get(pk=part_id)

            # Validate supplier exists
            supplier = Company.objects.get(pk=supplier_id)

            # Validate supplier is actually a supplier
            if not supplier.is_supplier:
                return False, f'{supplier.name} is not configured as a supplier'

            # Validate supplier-part relationship exists
            supplier_part = SupplierPart.objects.filter(
                part=part, supplier=supplier
            ).first()

            if not supplier_part:
                return (
                    False,
                    f'No supplier-part relationship found for {part.name} and {supplier.name}',
                )

            # Validate quantity
            if quantity <= 0:
                return False, 'Quantity must be greater than 0'

            # Check MOQ
            moq = supplier_part.minimum_order_quantity or Decimal('0')
            if quantity < float(moq):
                return (
                    False,
                    f'Quantity ({quantity}) below minimum order quantity ({moq})',
                )

            return True, ''

        except Part.DoesNotExist:
            return False, f'Part {part_id} not found'
        except Company.DoesNotExist:
            return False, f'Supplier {supplier_id} not found'
        except Exception as e:
            return False, f'Validation error: {str(e)}'

    def create_purchase_order(
        self,
        part_id: int,
        supplier_id: int,
        quantity: float,
        pipeline_id: str,
        approval_request_id: Optional[str] = None,
    ) -> int:
        """
        Create a PurchaseOrder in InvenTree.

        Args:
            part_id: ID of the part
            supplier_id: ID of the supplier
            quantity: Quantity to order
            pipeline_id: UUID of the pipeline execution
            approval_request_id: UUID of the approval request (optional)

        Returns:
            PurchaseOrder ID

        Raises:
            Exception if creation fails
        """
        # Validate data
        is_valid, error_message = self.validate_po_data(part_id, supplier_id, quantity)
        if not is_valid:
            raise Exception(f'PO validation failed: {error_message}')

        try:
            with transaction.atomic():
                # Get part and supplier
                part = Part.objects.get(pk=part_id)
                supplier = Company.objects.get(pk=supplier_id)

                # Get supplier part for pricing
                supplier_part = SupplierPart.objects.filter(
                    part=part, supplier=supplier
                ).first()

                # Create PurchaseOrder
                po = PurchaseOrder.objects.create(
                    supplier=supplier,
                    description=f'AI Procurement: {part.name}',
                    status=10,  # Pending/Draft status
                    reference=f'AI-{pipeline_id[:8]}',
                )

                # Create line item
                PurchaseOrderLineItem.objects.create(
                    order=po,
                    part=supplier_part,
                    quantity=Decimal(str(quantity)),
                    reference=f'Pipeline {pipeline_id[:8]}',
                    notes=f'Created by Agentic AI System. Pipeline ID: {pipeline_id}',
                )

                print(
                    f'Created PurchaseOrder {po.id} for {quantity} units of {part.name} from {supplier.name}'
                )

                return po.id

        except Exception as e:
            print(f'Error creating purchase order: {e}')
            raise Exception(f'Failed to create PurchaseOrder: {str(e)}')
