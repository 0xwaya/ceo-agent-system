"""
Persistence and Checkpointing Layer

Implements state persistence using LangGraph's checkpoint API with support for:
1. SQLite (local development)
2. PostgreSQL (production)
3. Custom checkpoint metadata
4. Recovery and replay
5. Multi-tenant isolation
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid
import json

from langgraph.checkpoint.memory import MemorySaver

try:
    from langgraph.checkpoint.sqlite import SqliteSaver

    SQLITE_AVAILABLE = True
except ImportError:
    SqliteSaver = None
    SQLITE_AVAILABLE = False

try:
    from langgraph.checkpoint.postgres import PostgresSaver

    POSTGRES_AVAILABLE = True
except ImportError:
    PostgresSaver = None
    POSTGRES_AVAILABLE = False

from graph_architecture.schemas import CheckpointMetadata, AgentRole

logger = logging.getLogger(__name__)


# ============================================================================
# CHECKPOINT FACTORY
# ============================================================================


def create_checkpointer(
    backend: str = "sqlite", connection_string: Optional[str] = None, **kwargs
) -> Any:
    """
    Create a checkpointer based on backend type

    Args:
        backend: 'sqlite', 'postgres', or 'memory'
        connection_string: Database connection string
        **kwargs: Additional backend-specific options

    Returns:
        Checkpointer instance

    Examples:
        >>> # Development
        >>> checkpointer = create_checkpointer("sqlite", "./checkpoints.db")

        >>> # Production
        >>> checkpointer = create_checkpointer(
        ...     "postgres",
        ...     "postgresql://user:pass@localhost:5432/checkpoints"
        ... )

        >>> # Testing
        >>> checkpointer = create_checkpointer("memory")
    """
    if backend == "sqlite":
        if not SQLITE_AVAILABLE:
            logger.warning(
                "SQLite checkpointer not available. Falling back to MemorySaver. "
                "Install with: pip install langgraph-checkpoint-sqlite"
            )
            return MemorySaver()
        path = connection_string or "./data/checkpoints.sqlite"
        logger.info(f"Creating SQLite checkpointer at {path}")
        # Create connection and return checkpointer
        import sqlite3

        conn = sqlite3.connect(path, check_same_thread=False)
        return SqliteSaver(conn)

    elif backend == "postgres":
        if not POSTGRES_AVAILABLE:
            raise ImportError(
                "PostgreSQL checkpointer not available. "
                "Install with: pip install langgraph-checkpoint-postgres"
            )
        if not connection_string:
            raise ValueError("PostgreSQL requires connection_string")
        logger.info(f"Creating PostgreSQL checkpointer")
        return PostgresSaver.from_conn_string(connection_string)

    elif backend == "memory":
        logger.warning("Using MemorySaver - checkpoints will not persist across restarts")
        return MemorySaver()

    else:
        raise ValueError(f"Unknown backend: {backend}")


# ============================================================================
# CHECKPOINT MANAGEMENT
# ============================================================================


class CheckpointManager:
    """
    High-level checkpoint management with metadata tracking
    """

    def __init__(self, checkpointer: Any):
        """
        Initialize checkpoint manager

        Args:
            checkpointer: LangGraph checkpointer instance
        """
        self.checkpointer = checkpointer
        self._metadata_cache: Dict[str, CheckpointMetadata] = {}

    def create_checkpoint_metadata(
        self,
        node_id: str,
        agent_role: AgentRole,
        thread_id: str,
        execution_step: int,
        total_nodes_visited: int,
        budget_spent: float = 0.0,
        api_calls_made: int = 0,
        is_terminal: bool = False,
        requires_approval: bool = False,
        parent_checkpoint_id: Optional[str] = None,
    ) -> CheckpointMetadata:
        """
        Create checkpoint metadata

        Args:
            node_id: Graph node identifier
            agent_role: Agent creating checkpoint
            thread_id: Execution thread
            execution_step: Current step number
            total_nodes_visited: Total nodes visited
            budget_spent: Budget spent so far
            api_calls_made: API calls made so far
            is_terminal: Is this a terminal state
            requires_approval: Waiting for user approval
            parent_checkpoint_id: Previous checkpoint ID

        Returns:
            CheckpointMetadata instance
        """
        checkpoint_id = f"ckpt-{uuid.uuid4().hex[:12]}"

        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            node_id=node_id,
            agent_role=agent_role,
            timestamp=datetime.now().isoformat(),
            thread_id=thread_id,
            parent_checkpoint_id=parent_checkpoint_id,
            execution_step=execution_step,
            total_nodes_visited=total_nodes_visited,
            budget_spent=budget_spent,
            api_calls_made=api_calls_made,
            is_terminal=is_terminal,
            requires_approval=requires_approval,
        )

        self._metadata_cache[checkpoint_id] = metadata

        logger.info(
            f"Created checkpoint {checkpoint_id} at node {node_id} "
            f"(step {execution_step}, agent: {agent_role})"
        )

        return metadata

    def get_metadata(self, checkpoint_id: str) -> Optional[CheckpointMetadata]:
        """Get checkpoint metadata"""
        return self._metadata_cache.get(checkpoint_id)

    def list_checkpoints(
        self, thread_id: str, limit: Optional[int] = None
    ) -> List[CheckpointMetadata]:
        """
        List checkpoints for a thread

        Args:
            thread_id: Thread identifier
            limit: Maximum number of checkpoints to return

        Returns:
            List of checkpoint metadata, most recent first
        """
        checkpoints = [
            meta for meta in self._metadata_cache.values() if meta.thread_id == thread_id
        ]

        # Sort by timestamp descending
        checkpoints.sort(key=lambda x: x.timestamp, reverse=True)

        if limit:
            checkpoints = checkpoints[:limit]

        return checkpoints

    def get_checkpoint_chain(self, checkpoint_id: str) -> List[CheckpointMetadata]:
        """
        Get full chain of checkpoints leading to given checkpoint

        Args:
            checkpoint_id: Final checkpoint in chain

        Returns:
            List of checkpoints from START to given checkpoint
        """
        chain = []
        current_id = checkpoint_id

        while current_id:
            metadata = self._metadata_cache.get(current_id)
            if not metadata:
                break

            chain.insert(0, metadata)
            current_id = metadata.parent_checkpoint_id

        return chain

    def find_approval_checkpoints(self, thread_id: str) -> List[CheckpointMetadata]:
        """
        Find all checkpoints requiring approval

        Args:
            thread_id: Thread identifier

        Returns:
            List of checkpoints waiting for approval
        """
        return [
            meta
            for meta in self._metadata_cache.values()
            if meta.thread_id == thread_id and meta.requires_approval
        ]


# ============================================================================
# RECOVERY AND REPLAY
# ============================================================================


class CheckpointRecovery:
    """
    Recovery and replay utilities
    """

    @staticmethod
    def get_latest_checkpoint(graph: Any, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Get latest checkpoint for thread

        Args:
            graph: Compiled LangGraph
            thread_id: Thread identifier

        Returns:
            Checkpoint state or None
        """
        config = {"configurable": {"thread_id": thread_id}}

        try:
            state = graph.get_state(config)
            return state.values if state else None
        except Exception as e:
            logger.error(f"Failed to get latest checkpoint: {e}")
            return None

    @staticmethod
    def resume_from_checkpoint(
        graph: Any, thread_id: str, override_state: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Resume execution from latest checkpoint

        Args:
            graph: Compiled LangGraph
            thread_id: Thread identifier
            override_state: Optional state updates before resuming

        Returns:
            Execution result
        """
        config = {"configurable": {"thread_id": thread_id}}

        if override_state:
            # Update state before resuming
            current_state = graph.get_state(config)
            if current_state and current_state.next:
                # Update state at current node
                graph.update_state(
                    config,
                    override_state,
                    as_node=current_state.next[0]
                    if isinstance(current_state.next, list)
                    else current_state.next,
                )

        # Continue execution
        logger.info(f"Resuming execution from checkpoint (thread: {thread_id})")
        return graph.invoke(None, config=config)

    @staticmethod
    def replay_to_checkpoint(graph: Any, thread_id: str, checkpoint_id: str) -> Any:
        """
        Time-travel to specific checkpoint and get state

        Args:
            graph: Compiled LangGraph
            thread_id: Thread identifier
            checkpoint_id: Target checkpoint

        Returns:
            State at that checkpoint
        """
        config = {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}

        try:
            state = graph.get_state(config)
            logger.info(f"Replayed to checkpoint {checkpoint_id}")
            return state.values if state else None
        except Exception as e:
            logger.error(f"Failed to replay to checkpoint: {e}")
            return None

    @staticmethod
    def get_execution_history(
        graph: Any, thread_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get full execution history for debugging

        Args:
            graph: Compiled LangGraph
            thread_id: Thread identifier
            limit: Maximum number of history entries

        Returns:
            List of state snapshots
        """
        config = {"configurable": {"thread_id": thread_id}}

        try:
            history = []
            for state in graph.get_state_history(config):
                history.append(
                    {
                        "checkpoint_id": state.checkpoint_id,
                        "next_node": state.next,
                        "values": state.values,
                        "metadata": state.config.get("configurable", {}),
                    }
                )

                if limit and len(history) >= limit:
                    break

            return history
        except Exception as e:
            logger.error(f"Failed to get execution history: {e}")
            return []


# ============================================================================
# MULTI-TENANT ISOLATION
# ============================================================================


class MultiTenantCheckpointer:
    """
    Multi-tenant checkpoint isolation
    """

    def __init__(self, checkpointer: Any):
        """
        Initialize multi-tenant checkpointer

        Args:
            checkpointer: Base checkpointer instance
        """
        self.checkpointer = checkpointer

    def create_tenant_config(
        self, tenant_id: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create tenant-isolated config

        Args:
            tenant_id: Tenant identifier
            session_id: Optional session identifier

        Returns:
            LangGraph config with tenant isolation
        """
        if not session_id:
            session_id = f"session-{uuid.uuid4().hex[:8]}"

        return {
            "configurable": {
                "thread_id": f"tenant-{tenant_id}-{session_id}",
                "checkpoint_ns": tenant_id,  # Namespace isolation
            }
        }

    def list_tenant_sessions(self, graph: Any, tenant_id: str) -> List[str]:
        """
        List all sessions for a tenant

        Args:
            graph: Compiled LangGraph
            tenant_id: Tenant identifier

        Returns:
            List of session IDs
        """
        # This would query the checkpointer storage
        # Implementation depends on backend
        logger.warning("list_tenant_sessions not fully implemented")
        return []

    def delete_tenant_data(self, tenant_id: str):
        """
        Delete all data for a tenant (GDPR compliance)

        Args:
            tenant_id: Tenant identifier
        """
        logger.warning(f"Delete tenant data for {tenant_id} - not implemented")
        # Implementation depends on backend


# ============================================================================
# CHECKPOINT EXPORT/IMPORT
# ============================================================================


def export_checkpoint(
    graph: Any,
    thread_id: str,
    checkpoint_id: Optional[str] = None,
    output_file: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Export checkpoint to JSON

    Args:
        graph: Compiled LangGraph
        thread_id: Thread identifier
        checkpoint_id: Specific checkpoint (None = latest)
        output_file: Optional file path to save JSON

    Returns:
        Checkpoint data
    """
    config = {"configurable": {"thread_id": thread_id}}
    if checkpoint_id:
        config["configurable"]["checkpoint_id"] = checkpoint_id

    state = graph.get_state(config)

    export_data = {
        "thread_id": thread_id,
        "checkpoint_id": checkpoint_id,
        "timestamp": datetime.now().isoformat(),
        "state": state.values if state else None,
        "next_node": state.next if state else None,
    }

    if output_file:
        with open(output_file, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        logger.info(f"Exported checkpoint to {output_file}")

    return export_data


def import_checkpoint(graph: Any, import_file: str, new_thread_id: Optional[str] = None) -> str:
    """
    Import checkpoint from JSON

    Args:
        graph: Compiled LangGraph
        import_file: JSON file path
        new_thread_id: Optional new thread ID

    Returns:
        Thread ID of imported checkpoint
    """
    with open(import_file, "r") as f:
        data = json.load(f)

    thread_id = new_thread_id or data["thread_id"]
    config = {"configurable": {"thread_id": thread_id}}

    # Import state
    if data["state"]:
        graph.update_state(config, data["state"], as_node=data.get("next_node", "START"))

    logger.info(f"Imported checkpoint to thread {thread_id}")
    return thread_id
