"""LangGraph workflow graph definition for procurement pipeline."""

from typing import Any, Dict

from langgraph.graph import END, StateGraph

from .state_manager import PipelineState, StateManager


def data_collection_node(state: PipelineState) -> PipelineState:
    """
    Node 1: Data collection - gather part and stock information.

    Args:
        state: Current pipeline state

    Returns:
        Updated state with collected data
    """
    from part.models import Part
    from stock.models import StockItem

    try:
        part = Part.objects.get(pk=state['part_id'])
        stock_items = StockItem.objects.filter(part=part)
        total_stock = sum(item.quantity for item in stock_items)

        state['agent_outputs']['data_collection'] = {
            'part_name': part.name,
            'current_stock': float(total_stock),
            'minimum_stock': float(part.minimum_stock or 0),
            'part_category_id': part.category_id if part.category else None,
        }
        state['current_node'] = 'demand_forecasting'
    except Exception as e:
        state['status'] = 'failed'
        state['error_message'] = f'Data collection failed: {str(e)}'

    return state


def demand_forecasting_node(state: PipelineState) -> PipelineState:
    """
    Node 2: Demand forecasting using Prophet.

    Args:
        state: Current pipeline state

    Returns:
        Updated state with forecast results
    """
    # Import here to avoid circular dependencies
    from .agents.demand_agent import DemandAgent

    try:
        demand_agent = DemandAgent()
        forecast_result = demand_agent.forecast_demand(
            state['part_id'], forecast_days=30
        )

        state['agent_outputs']['forecast'] = forecast_result
        state['current_node'] = 'supplier_ranking'
    except Exception as e:
        state['status'] = 'failed'
        state['error_message'] = f'Demand forecasting failed: {str(e)}'

    return state


def supplier_ranking_node(state: PipelineState) -> PipelineState:
    """
    Node 3: Supplier ranking using multi-criteria analysis.

    Args:
        state: Current pipeline state

    Returns:
        Updated state with supplier rankings
    """
    # Import here to avoid circular dependencies
    from .agents.supplier_agent import SupplierAgent

    try:
        supplier_agent = SupplierAgent()
        forecast = state['agent_outputs']['forecast']
        required_quantity = forecast['predicted_demand']

        supplier_rankings = supplier_agent.rank_suppliers(
            state['part_id'], required_quantity
        )

        state['agent_outputs']['suppliers'] = supplier_rankings
        state['current_node'] = 'decision_making'
    except Exception as e:
        state['status'] = 'failed'
        state['error_message'] = f'Supplier ranking failed: {str(e)}'

    return state


def decision_making_node(state: PipelineState) -> PipelineState:
    """
    Node 4: Decision making using Ollama LLM.

    Args:
        state: Current pipeline state

    Returns:
        Updated state with procurement decision
    """
    # Import here to avoid circular dependencies
    from .agents.decision_agent import DecisionAgent

    try:
        decision_agent = DecisionAgent()

        # Build decision context
        data_collection = state['agent_outputs']['data_collection']
        forecast = state['agent_outputs']['forecast']
        suppliers = state['agent_outputs']['suppliers']

        decision_context = {
            'part_id': state['part_id'],
            'part_name': data_collection['part_name'],
            'current_stock': data_collection['current_stock'],
            'minimum_stock': data_collection['minimum_stock'],
            'forecasted_demand': forecast['predicted_demand'],
            'confidence_interval': (
                forecast['confidence_lower'],
                forecast['confidence_upper'],
            ),
            'trend_direction': forecast.get('trend_direction', 'unknown'),
            'top_suppliers': suppliers[:3],  # Top 3 only
        }

        procurement_decision = decision_agent.make_decision(decision_context)

        state['agent_outputs']['decision'] = procurement_decision
        state['current_node'] = 'human_approval'
    except Exception as e:
        state['status'] = 'failed'
        state['error_message'] = f'Decision making failed: {str(e)}'

    return state


def human_approval_node(state: PipelineState) -> PipelineState:
    """
    Node 5: Human approval gate (interrupt point).

    This node creates an approval request and interrupts the pipeline.
    The pipeline will resume when a human responds.

    Args:
        state: Current pipeline state

    Returns:
        Updated state with approval request
    """
    # Import here to avoid circular dependencies
    from .approval_gate import ApprovalGate

    try:
        approval_gate = ApprovalGate()
        approval_request = approval_gate.create_approval_request(
            state['pipeline_id'], state['agent_outputs']['decision']
        )

        state['agent_outputs']['approval_request_id'] = str(approval_request.id)
        state['status'] = 'interrupted'

        # Send notifications
        approval_gate.send_notifications(approval_request)

        # Pipeline will wait here until human responds
    except Exception as e:
        state['status'] = 'failed'
        state['error_message'] = f'Approval gate failed: {str(e)}'

    return state


def execution_node(state: PipelineState) -> PipelineState:
    """
    Node 6: Execute procurement by creating PurchaseOrder.

    Args:
        state: Current pipeline state

    Returns:
        Updated state with execution results
    """
    # Import here to avoid circular dependencies
    from .agents.execution_agent import ExecutionAgent

    try:
        execution_agent = ExecutionAgent()

        # Get human decision
        human_decision = state.get('human_decision', {})
        action = human_decision.get('action', 'approve')

        if action == 'reject':
            state['status'] = 'rejected'
            state['current_node'] = 'completed'
            return state

        # Get decision data
        decision = state['agent_outputs']['decision']

        # Use modified values if provided
        quantity = human_decision.get('modified_quantity') or decision[
            'recommended_quantity'
        ]
        supplier_id = human_decision.get('modified_supplier_id') or decision.get(
            'recommended_supplier_id'
        )

        # Create purchase order
        po_id = execution_agent.create_purchase_order(
            part_id=state['part_id'],
            supplier_id=supplier_id,
            quantity=quantity,
            pipeline_id=state['pipeline_id'],
            approval_request_id=state['agent_outputs'].get('approval_request_id'),
        )

        state['agent_outputs']['po_id'] = po_id
        state['current_node'] = 'learning_update'
    except Exception as e:
        state['status'] = 'failed'
        state['error_message'] = f'Execution failed: {str(e)}'

    return state


def learning_update_node(state: PipelineState) -> PipelineState:
    """
    Node 7: Update learning layer with outcome.

    Args:
        state: Current pipeline state

    Returns:
        Updated state with learning results
    """
    # Import here to avoid circular dependencies
    from .learning.learning_layer import LearningLayer

    try:
        learning_layer = LearningLayer()

        # Prepare outcome data
        decision = state['agent_outputs']['decision']
        forecast = state['agent_outputs']['forecast']

        outcome_data = {
            'decision_made': 'ORDER',
            'quantity_ordered': state['agent_outputs'].get('po_id')
            and decision['recommended_quantity']
            or 0,
            'supplier_used': decision.get('recommended_supplier_id'),
            'po_id': state['agent_outputs'].get('po_id'),
            'forecast_demand': forecast['predicted_demand'],
        }

        # Log outcome
        learning_layer.log_outcome(state['pipeline_id'], outcome_data)

        state['agent_outputs']['learning_applied'] = True
        state['status'] = 'completed'
        state['current_node'] = 'completed'
    except Exception as e:
        state['status'] = 'failed'
        state['error_message'] = f'Learning update failed: {str(e)}'

    return state


def should_continue_to_execution(state: PipelineState) -> str:
    """
    Conditional edge: Determine if pipeline should continue to execution.

    Args:
        state: Current pipeline state

    Returns:
        Next node name or END
    """
    if state['status'] == 'interrupted':
        # Wait for human approval
        return END
    elif state['status'] == 'failed':
        return END
    else:
        return 'execution'


def define_procurement_graph() -> StateGraph:
    """
    Define the LangGraph workflow for procurement pipeline.

    Returns:
        Configured StateGraph instance
    """
    # Create graph
    workflow = StateGraph(PipelineState)

    # Add nodes
    workflow.add_node('data_collection', data_collection_node)
    workflow.add_node('demand_forecasting', demand_forecasting_node)
    workflow.add_node('supplier_ranking', supplier_ranking_node)
    workflow.add_node('decision_making', decision_making_node)
    workflow.add_node('human_approval', human_approval_node)
    workflow.add_node('execution', execution_node)
    workflow.add_node('learning_update', learning_update_node)

    # Define edges
    workflow.add_edge('data_collection', 'demand_forecasting')
    workflow.add_edge('demand_forecasting', 'supplier_ranking')
    workflow.add_edge('supplier_ranking', 'decision_making')
    workflow.add_edge('decision_making', 'human_approval')

    # Conditional edge from human_approval
    # This is where the interrupt happens - pipeline waits for human input
    workflow.add_conditional_edges(
        'human_approval', should_continue_to_execution, {'execution': 'execution', END: END}
    )

    workflow.add_edge('execution', 'learning_update')
    workflow.add_edge('learning_update', END)

    # Set entry point
    workflow.set_entry_point('data_collection')

    return workflow


def compile_procurement_graph() -> Any:
    """
    Compile the procurement graph with PostgreSQL checkpointer.

    Returns:
        Compiled graph ready for execution
    """
    state_manager = StateManager()
    workflow = define_procurement_graph()

    # Compile with checkpointer for state persistence
    compiled_graph = workflow.compile(checkpointer=state_manager.checkpointer)

    return compiled_graph
