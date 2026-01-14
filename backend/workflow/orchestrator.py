"""
Workflow Orchestrator
Session manager for multi-agent system.
Agents self-deploy and react to events; orchestrator manages lifecycle and timing.
"""

from typing import Dict, Optional, Callable
import asyncio
from coordination.message_bus import MessageBus, MessageType
from coordination.agent_registry import AgentRegistry
from coordination.role_policy import RolePolicyEngine
from agents import (
    FactorExtractionAgent,
    SupportingAgent,
    CriticAgent,
    SynthesizerAgent,
    FinalDecisionAgent
)
from llm.llm_client import LLMClient


class Orchestrator:
    """
    Session manager for multi-agent system.
    Agents are self-deployed and event-driven; orchestrator manages timing and lifecycle.
    """
    
    def __init__(self, llm_client: LLMClient):
        # Initialize coordination layer
        self.message_bus = MessageBus()
        self.registry = AgentRegistry()
        self.policy_engine = RolePolicyEngine()
        
        self.llm_client = llm_client
        
        # Initialize validation components
        from validation import FactorValidator, AssumptionTracker, ResolutionTracker, IntegrityChecker
        self.factor_validator = FactorValidator()
        self.assumption_tracker = AssumptionTracker()
        self.resolution_tracker = ResolutionTracker()
        self.integrity_checker = IntegrityChecker()
        
        # Initialize agents (they self-register) with validation components
        self.factor_agent = FactorExtractionAgent(
            self.message_bus, llm_client, self.registry, self.policy_engine,
            factor_validator=self.factor_validator
        )
        self.support_agent = SupportingAgent(
            self.message_bus, llm_client, self.registry, self.policy_engine,
            assumption_tracker=self.assumption_tracker,
            resolution_tracker=self.resolution_tracker
        )
        self.critic_agent = CriticAgent(
            self.message_bus, llm_client, self.registry, self.policy_engine,
            resolution_tracker=self.resolution_tracker
        )
        self.synthesizer_agent = SynthesizerAgent(
            self.message_bus, llm_client, self.registry, self.policy_engine,
            resolution_tracker=self.resolution_tracker
        )
        self.final_agent = FinalDecisionAgent(
            self.message_bus, llm_client, self.registry, self.policy_engine
        )
        
        self.progress_callback: Optional[Callable] = None
        self.current_input_text: str = ""
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for real-time progress updates."""
        self.progress_callback = callback
    
    def _notify_progress(self, stage: str, message: str, data: Optional[Dict] = None):
        """Notify progress updates."""
        if self.progress_callback:
            self.progress_callback({
                "stage": stage,
                "message": message,
                "data": data or {}
            })
    
    async def analyze(self, input_text: str, show_updates: bool = True) -> Dict:
        """
        Execute the complete analysis workflow.
        Agents react to events; orchestrator manages timing and lifecycle.
        """
        
        # Clear previous state
        self.message_bus.clear()
        self.assumption_tracker.clear()
        self.resolution_tracker.clear()
        self.integrity_checker.clear()
        self.current_input_text = input_text
        
        # Set input text context for agents
        self.factor_agent.current_input_text = input_text
        self.support_agent.current_input_text = input_text
        self.critic_agent.current_input_text = input_text
        self.synthesizer_agent.current_input_text = input_text
        
        try:
            # STEP 1: Trigger factor extraction
            if show_updates:
                self._notify_progress("factor_extraction", "Extracting key factors...")
            
            factors = await self.factor_agent.process(input_text)
            
            # Factor extraction publishes FACTOR_DISCOVERED events
            # Supporting agents react automatically via subscriptions
            
            if show_updates:
                self._notify_progress("factor_extraction", f"Extracted {len(factors)} factors", {
                    "factors": factors
                })
            
            # STEP 2: Orchestrate debate for each factor
            # Supporting agents react to FACTOR_DISCOVERED → generate SUPPORT_ARGUMENT
            # Critic agents react to SUPPORT_ARGUMENT → generate CRITIQUE
            # Supporting agents react to CRITIQUE → generate REBUTTAL (dynamic)
            
            if show_updates:
                self._notify_progress("debate", "Starting agent debates...")
            
            # For each factor, orchestrate the debate
            for factor in factors:
                factor_id = factor['id']
                
                if show_updates:
                    self._notify_progress("debate", f"Debating factor {factor_id}: {factor['name']}")
                
                # Step 2a: Supporting agent generates support
                support = await self.support_agent.support_factor(factor, input_text)
                
                # Step 2b: Critic agent generates critique
                critique = await self.critic_agent.critique_factor(factor, support, input_text)
                
                # Step 2c: Supporting agent may issue rebuttal
                if critique and critique.get('resolution') != 'ACCEPTED':
                    rebuttal = await self.support_agent.rebut(factor_id, critique, input_text)
                    
                    if show_updates:
                        resolution = critique.get('resolution', 'UNKNOWN')
                        self._notify_progress("debate", f"Factor {factor_id} resolved: {resolution}")
            
            if show_updates:
                self._notify_progress("debate", "All debates completed")
            
            # STEP 3: Trigger synthesis
            if show_updates:
                self._notify_progress("synthesis", "Synthesizing insights from all debates...")
            
            synthesis = await self.synthesizer_agent.synthesize(input_text)
            
            if show_updates:
                self._notify_progress("synthesis", "Synthesis complete", {
                    "synthesis": synthesis
                })
            
            # STEP 4: Trigger final report
            if show_updates:
                self._notify_progress("final", "Generating final report...")
            
            final_report = await self.final_agent.generate_final_report(input_text)
            
            if show_updates:
                self._notify_progress("final", "Analysis complete!", {
                    "report": final_report
                })
            
            # STEP 5: Run integrity checks
            if show_updates:
                self._notify_progress("validation", "Running integrity checks...")
            
            # Get validation results from factor extraction
            validation_results = None
            factor_list_msg = next(
                (msg for msg in self.message_bus.get_all_messages() 
                 if msg.get('type') == MessageType.FACTOR_LIST.value),
                None
            )
            if factor_list_msg:
                validation_results = factor_list_msg.get('validation_results')
            
            # Run integrity checks
            if validation_results:
                self.integrity_checker.check_synthesis_validity(
                    factors, validation_results, self.resolution_tracker, synthesis
                )
            
            integrity_report = self.integrity_checker.get_integrity_report()
            integrity_summary = self.integrity_checker.get_integrity_summary()
            
            if show_updates:
                self._notify_progress("validation", "Integrity checks complete", {
                    "integrity": integrity_summary
                })
            
            # Compile complete results with validation
            return {
                "success": True,
                "factors": factors,
                "validation_results": validation_results,
                "debates": self.message_bus.get_debate_summary(),
                "synthesis": synthesis,
                "final_report": final_report,
                "assumptions": self.assumption_tracker.get_all_assumptions(),
                "resolutions": {
                    "accepted": self.resolution_tracker.get_accepted_factors(),
                    "partially_accepted": self.resolution_tracker.get_partially_accepted_factors(),
                    "rejected": self.resolution_tracker.get_rejected_factors()
                },
                "integrity_check": integrity_summary,
                "integrity_report": integrity_report,
                "all_messages": self.message_bus.get_all_messages(),
                "registry": {
                    "agents": [agent.agent_id for agent in self.registry.list_all_agents()]
                }
            }
        
        except Exception as e:
            if show_updates:
                self._notify_progress("error", f"Error during analysis: {str(e)}")
            
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "factors": self.message_bus.get_factors(),
                "all_messages": self.message_bus.get_all_messages()
            }
    
    async def _wait_for_debate_completion(self, factors: list, show_updates: bool, timeout: float = 60.0):
        """Wait for debate to complete - all factors have support and critique."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if all factors have support and critique
            all_complete = True
            for factor in factors:
                factor_id = factor['id']
                supports = self.message_bus.get_messages_by_type(
                    MessageType.SUPPORT_ARGUMENT
                )
                critiques = self.message_bus.get_messages_by_type(
                    MessageType.CRITIQUE
                )
                
                has_support = any(s.get('factor_id') == factor_id for s in supports)
                has_critique = any(c.get('factor_id') == factor_id for c in critiques)
                
                if not (has_support and has_critique):
                    all_complete = False
                    break
            
            if all_complete:
                break
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                if show_updates:
                    self._notify_progress("debate", "Debate timeout reached, proceeding...")
                break
            
            # Wait a bit before checking again
            await asyncio.sleep(0.5)

