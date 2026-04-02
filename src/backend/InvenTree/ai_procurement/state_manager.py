"""LangGraph State Manager for Agentic AI Procurement Pipeline."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from django.conf import settings
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import StateGraph

from .models import PipelineExecution


class PipelineState(TypedDict):
    """State structure for procurement pipeline."""

    pipeline_id: str
    part_id: int
    current_node: str
    agent_outputs: Dict[str, Any]
    human_decision: Optional[Dict[str, Any]]
    status: str
    trigger_reason: str
    error_message: Optional[str]


class StateManager:
    """Manages LangGraph pipeline state with database persistence."""

    def __init__(self):
        """Initialize state manager with appropriate checkpointer based on database backend."""
        # Get database configuration from Django settings
        db_config = settings.DATABASES['default']
        db_engine = db_config.get('ENGINE', '')
        
        # Determine which checkpointer to use based on database backend
        if 'postgresql' in db_engine or 'postgres' in db_engine:
            # Use PostgreSQL checkpointer for PostgreSQL databases
            self.connection_string = (
                f"postgresql://{db_config['USER']}:{db_config['PASSWORD']}"
                f"@{db_config['HOST']}:{db_config.get('PORT', 5432)}/{db_config['NAME']}"
            )
            self._use_postgres = True
        else:
            # Use in-memory checkpointer for SQLite and other databases
            # Note: InMemorySaver doesn't persist across restarts, but works for development
            self._use_postgres = False
        
        # Defer checkpointer initialization until first use
        self._checkpointer = None

    @property
    def checkpointer(self):
        """Lazy initialization of checkpointer."""
        if self._checkpointer is None:
            if self._use_postgres:
                self._checkpointer = PostgresSaver(self.connection_string)
                self._checkpointer.setup()
            else:
                # Use in-memory checkpointer for non-PostgreSQL databases
                self._checkpointer = InMemorySaver()
        return self._checkpointer

    def initialize_pipeline(
        self, part_id: int, trigger_reason: str
    ) -> tuple[str, PipelineState]:
        """
        Initialize a new pipeline execution.

        Args:
            part_id: ID of the part triggering the pipeline
            trigger_reason: Reason for pipeline trigger

        Returns:
            Tuple of (pipeline_id, initial_state)
        """
        pipeline_id = str(uuid.uuid4())

        # Create database record
        pipeline_execution = PipelineExecution.objects.create(
            id=pipeline_id,
            part_id=part_id,
            trigger_reason=trigger_reason,
            status='running',
            current_node='data_collection',
            state_data={},
        )

        # Create initial state
        initial_state: PipelineState = {
            'pipeline_id': pipeline_id,
            'part_id': part_id,
            'current_node': 'data_collection',
            'agent_outputs': {},
            'human_decision': None,
            'status': 'running',
            'trigger_reason': trigger_reason,
            'error_message': None,
        }

        return pipeline_id, initial_state

    def persist_checkpoint(self, pipeline_id: str, state: PipelineState) -> bool:
        """
        Persist pipeline state to PostgreSQL.

        Args:
            pipeline_id: UUID of the pipeline
            state: Current pipeline state

        Returns:
            True if successful, False otherwise
        """
        try:
            # Update database record
            PipelineExecution.objects.filter(id=pipeline_id).update(
                current_node=state['current_node'],
                status=state['status'],
                state_data=state['agent_outputs'],
                error_message=state.get('error_message'),
                updated_at=datetime.now(),
            )

            # Persist to LangGraph checkpointer
            config = {'configurable': {'thread_id': pipeline_id}}
            self.checkpointer.put(config, state, {})

            return True
        except Exception as e:
            print(f'Error persisting checkpoint: {e}')
            return False

    def load_checkpoint(self, pipeline_id: str) -> Optional[PipelineState]:
        """
        Load pipeline state from PostgreSQL.

        Args:
            pipeline_id: UUID of the pipeline

        Returns:
            Pipeline state if found, None otherwise
        """
        try:
            # Load from database
            pipeline = PipelineExecution.objects.get(id=pipeline_id)

            # Reconstruct state
            state: PipelineState = {
                'pipeline_id': str(pipeline.id),
                'part_id': pipeline.part_id,
                'current_node': pipeline.current_node,
                'agent_outputs': pipeline.state_data or {},
                'human_decision': None,
                'status': pipeline.status,
                'trigger_reason': pipeline.trigger_reason,
                'error_message': pipeline.error_message,
            }

            return state
        except PipelineExecution.DoesNotExist:
            return None
        except Exception as e:
            print(f'Error loading checkpoint: {e}')
            return None

    def interrupt_pipeline(self, pipeline_id: str, interrupt_reason: str) -> bool:
        """
        Interrupt pipeline execution for human approval.

        Args:
            pipeline_id: UUID of the pipeline
            interrupt_reason: Reason for interruption

        Returns:
            True if successful, False otherwise
        """
        try:
            PipelineExecution.objects.filter(id=pipeline_id).update(
                status='interrupted',
                current_node='human_approval',
                updated_at=datetime.now(),
            )
            return True
        except Exception as e:
            print(f'Error interrupting pipeline: {e}')
            return False

    def resume_pipeline(
        self, pipeline_id: str, human_decision: Dict[str, Any]
    ) -> Optional[PipelineState]:
        """
        Resume pipeline execution after human approval.

        Args:
            pipeline_id: UUID of the pipeline
            human_decision: Human approval decision data

        Returns:
            Updated pipeline state if successful, None otherwise
        """
        try:
            # Load current state
            state = self.load_checkpoint(pipeline_id)
            if not state:
                return None

            # Update state with human decision
            state['human_decision'] = human_decision
            state['status'] = 'running'
            state['current_node'] = 'execution'

            # Persist updated state
            self.persist_checkpoint(pipeline_id, state)

            # Update database
            PipelineExecution.objects.filter(id=pipeline_id).update(
                status='running',
                current_node='execution',
                updated_at=datetime.now(),
            )

            return state
        except Exception as e:
            print(f'Error resuming pipeline: {e}')
            return None

    def mark_pipeline_complete(
        self, pipeline_id: str, final_status: str = 'completed'
    ) -> bool:
        """
        Mark pipeline as complete.

        Args:
            pipeline_id: UUID of the pipeline
            final_status: Final status (completed, failed, rejected)

        Returns:
            True if successful, False otherwise
        """
        try:
            PipelineExecution.objects.filter(id=pipeline_id).update(
                status=final_status,
                current_node='completed',
                completed_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return True
        except Exception as e:
            print(f'Error marking pipeline complete: {e}')
            return False

    def get_pipeline_status(self, pipeline_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current pipeline status.

        Args:
            pipeline_id: UUID of the pipeline

        Returns:
            Dictionary with pipeline status information
        """
        try:
            pipeline = PipelineExecution.objects.get(id=pipeline_id)
            return {
                'pipeline_id': str(pipeline.id),
                'part_id': pipeline.part_id,
                'status': pipeline.status,
                'current_node': pipeline.current_node,
                'trigger_reason': pipeline.trigger_reason,
                'created_at': pipeline.created_at.isoformat(),
                'updated_at': pipeline.updated_at.isoformat(),
                'completed_at': (
                    pipeline.completed_at.isoformat()
                    if pipeline.completed_at
                    else None
                ),
                'error_message': pipeline.error_message,
            }
        except PipelineExecution.DoesNotExist:
            return None
        except Exception as e:
            print(f'Error getting pipeline status: {e}')
            return None

    def mark_pipeline_failed(self, pipeline_id: str, error_message: str) -> bool:
        """
        Mark pipeline as failed.

        Args:
            pipeline_id: UUID of the pipeline
            error_message: Error message describing the failure

        Returns:
            True if successful, False otherwise
        """
        try:
            PipelineExecution.objects.filter(id=pipeline_id).update(
                status='failed',
                error_message=error_message,
                completed_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return True
        except Exception as e:
            print(f'Error marking pipeline as failed: {e}')
            return False

    def mark_pipeline_rejected(self, pipeline_id: str, reason: str) -> bool:
        """
        Mark pipeline as rejected.

        Args:
            pipeline_id: UUID of the pipeline
            reason: Reason for rejection

        Returns:
            True if successful, False otherwise
        """
        try:
            PipelineExecution.objects.filter(id=pipeline_id).update(
                status='rejected',
                error_message=reason,
                completed_at=datetime.now(),
                updated_at=datetime.now(),
            )
            return True
        except Exception as e:
            print(f'Error marking pipeline as rejected: {e}')
            return False
