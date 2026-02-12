"""
Analysis Service - CFO Strategic Analysis
Business logic for strategic objective analysis
"""

import logging
from typing import Dict, Any
from datetime import datetime

from services.state_builder import CFOStateBuilder
from agents.cfo_agent import analyze_strategic_objectives
from utils.constants import AppConstants
from exceptions import ValidationError, AnalysisError

logger = logging.getLogger(__name__)


class AnalysisService:
    """
    Service for CFO strategic analysis operations
    Handles business logic separate from API routes
    """
    
    def __init__(self):
        """Initialize analysis service"""
        self.state_builder = CFOStateBuilder()
    
    def analyze_objectives(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform strategic analysis on company objectives
        
        Args:
            request_data: Validated request data from API
            
        Returns:
            Analysis results with tasks, budget allocation, risks
            
        Raises:
            ValidationError: If request data is invalid
            AnalysisError: If analysis fails
        """
        print(f"\n=== ANALYSIS SERVICE DEBUG ===")
        print(f"Request data: {request_data}")
        logger.info("Starting strategic analysis", extra={'data': request_data})
        
        try:
            # Create initial state
            state = self.state_builder.create_from_request(request_data)
            
            print(f"Created state keys: {list(state.keys())}")
            print(f"company_name in state: {state.get('company_name')}")
            
            logger.info(f"Created state: company={state.get('company_name')}, industry={state.get('industry')}")
            
            # Validate state
            is_valid, error_msg = self.state_builder.validate_state(state)
            if not is_valid:
                logger.error(f"State validation failed: {error_msg}")
                raise ValidationError(error_msg)
            
            logger.info("Running CFO strategic analysis...")
            print(f"About to call analyze_strategic_objectives...")
            
            # Execute analysis
            result = analyze_strategic_objectives(state)
            
            print(f"Analysis complete!")

            
            tasks = result.get('identified_tasks', [])
            budget_allocation = result.get('budget_allocated', {})
            risks = result.get('risks', [])
            timeline = result.get('target_completion_days', AppConstants.DEFAULT_TIMELINE_DAYS)
            
            logger.info(
                f"Analysis complete. Tasks: {len(tasks)}, "
                f"Budget allocated: ${sum(budget_allocation.values()):.2f}"
            )
            
            return {
                'success': True,
                'tasks': tasks,
                'budget_allocation': budget_allocation,
                'risks': risks,
                'timeline': timeline,
                'message': AppConstants.MSG_ANALYSIS_COMPLETE
            }
            
        except ValidationError:
            logger.error("Validation failed", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}", exc_info=True)
            raise AnalysisError(f"Strategic analysis failed: {str(e)}")
    
    def get_analysis_summary(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get summary of analysis results
        
        Args:
            state: CFO agent state
            
        Returns:
            Summary dictionary
        """
        return {
            'total_tasks': len(state.get('identified_tasks', [])),
            'total_budget': state.get('total_budget', 0),
            'budget_allocated': sum(state.get('budget_allocated', {}).values()),
            'budget_remaining': state.get('budget_remaining', 0),
            'risks_identified': len(state.get('risks', [])),
            'opportunities_identified': len(state.get('opportunities', [])),
            'current_phase': state.get('current_phase', 'unknown'),
            'completion_percentage': self._calculate_completion(state)
        }
    
    @staticmethod
    def _calculate_completion(state: Dict[str, Any]) -> float:
        """Calculate completion percentage"""
        total_tasks = len(state.get('identified_tasks', []))
        completed_tasks = len(state.get('completed_tasks', []))
        
        if total_tasks == 0:
            return 0.0
        
        return round((completed_tasks / total_tasks) * 100, 2)
