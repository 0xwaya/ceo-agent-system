"""
Orchestration Service
Handles full multi-agent orchestration workflow
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

from services.state_builder import CFOStateBuilder
from services.analysis_service import AnalysisService
from agents.ceo_agent import analyze_strategic_objectives as ceo_analyze
from utils.constants import AppConstants

logger = logging.getLogger(__name__)


class OrchestrationService:
    """
    Service for full CFO orchestration operations
    Manages background threads and SocketIO communication
    """

    def __init__(self, socketio=None):
        """
        Initialize orchestration service

        Args:
            socketio: Flask-SocketIO instance for real-time updates
        """
        self.socketio = socketio
        self.state_builder = CFOStateBuilder()
        self.analysis_service = AnalysisService()
        self.executor = ThreadPoolExecutor(max_workers=AppConstants.MAX_ORCHESTRATION_THREADS)
        self.active_jobs: Dict[str, Future] = {}

    def execute_full_orchestration_async(
        self, request_data: Dict[str, Any], session_id: Optional[str] = None
    ) -> str:
        """
        Execute full orchestration in background thread

        Args:
            request_data: Request data with company info and objectives
            session_id: Optional session identifier

        Returns:
            Job ID for tracking
        """
        job_id = session_id or str(uuid.uuid4())

        logger.info(f"Starting orchestration job {job_id}")

        # Submit to thread pool
        future = self.executor.submit(self._run_orchestration, request_data, job_id)

        self.active_jobs[job_id] = future

        return job_id

    def _run_orchestration(self, request_data: Dict[str, Any], job_id: str):
        """
        Run orchestration in background

        Args:
            request_data: Request data
            job_id: Job identifier
        """
        try:
            logger.info(f"Orchestration {job_id} started")
            self._emit(
                "orchestration_started",
                {"job_id": job_id, "timestamp": datetime.now().isoformat()},
            )

            # Create state
            state = self.state_builder.create_from_request(request_data)

            # Phase 1: Strategic Analysis
            logger.info("Phase 1: Strategic Analysis")
            self._emit(
                "phase",
                {"name": "Strategic Analysis", "status": "running", "job_id": job_id},
            )

            state = ceo_analyze(state)

            self._emit(
                "phase",
                {
                    "name": "Strategic Analysis",
                    "status": "complete",
                    "tasks": state.get("identified_tasks", []),
                    "job_id": job_id,
                },
            )

            logger.info(
                f"Strategic analysis complete. Tasks: {len(state.get('identified_tasks', []))}"
            )

            # Phase 2: Agent Deployment
            logger.info("Phase 2: Agent Deployment")
            self._emit(
                "phase",
                {"name": "Agent Deployment", "status": "running", "job_id": job_id},
            )

            # Deploy agents for first N tasks (demo mode)
            tasks = state.get("identified_tasks", [])[: AppConstants.DEMO_TASK_LIMIT]

            for task in tasks:
                agent_type = task.get("required_expertise", "").lower()
                task_id = task.get("task_id", "unknown")

                logger.info(f"Deploying {agent_type} agent for task {task_id}")

                self._emit(
                    "agent_deploying",
                    {"agent": agent_type, "task": task_id, "job_id": job_id},
                )

                # Simulate processing
                time.sleep(AppConstants.TASK_PROCESSING_DELAY)

                self._emit(
                    "agent_deployed",
                    {"agent": agent_type, "status": "success", "job_id": job_id},
                )

            # Calculate budget used
            budget_used = sum(state.get("budget_allocated", {}).values())

            logger.info(f"Orchestration {job_id} complete. Budget used: ${budget_used}")

            self._emit(
                "orchestration_complete",
                {
                    "status": "success",
                    "budget_used": budget_used,
                    "tasks_deployed": len(tasks),
                    "timestamp": datetime.now().isoformat(),
                    "job_id": job_id,
                },
            )

        except Exception as e:
            logger.error(f"Orchestration {job_id} failed: {str(e)}", exc_info=True)
            self._emit(
                "orchestration_error",
                {
                    "error": str(e),
                    "job_id": job_id,
                    "timestamp": datetime.now().isoformat(),
                },
            )
        finally:
            # Cleanup
            self.active_jobs.pop(job_id, None)
            logger.info(f"Orchestration {job_id} finished")

    def _emit(self, event: str, data: Dict[str, Any]):
        """
        Emit SocketIO event safely

        Args:
            event: Event name
            data: Event data
        """
        if self.socketio:
            try:
                self.socketio.emit(event, data, broadcast=True)
            except Exception as e:
                logger.error(f"Failed to emit {event}: {e}")
        else:
            logger.warning(f"No SocketIO instance, cannot emit {event}")

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of orchestration job

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary or None if not found
        """
        future = self.active_jobs.get(job_id)
        if not future:
            return None

        return {
            "job_id": job_id,
            "running": future.running(),
            "done": future.done(),
            "cancelled": future.cancelled(),
        }

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel orchestration job

        Args:
            job_id: Job identifier

        Returns:
            True if cancelled, False otherwise
        """
        future = self.active_jobs.get(job_id)
        if future and not future.done():
            future.cancel()
            self.active_jobs.pop(job_id, None)
            logger.info(f"Orchestration {job_id} cancelled")
            return True
        return False

    def shutdown(self):
        """Shutdown orchestration service and cleanup threads"""
        logger.info("Shutting down orchestration service")
        self.executor.shutdown(wait=True)
        self.active_jobs.clear()
