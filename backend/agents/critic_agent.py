"""
Critic Agent
Argues AGAINST each factor, identifying flaws, risks, and alternative explanations.
Reactive: automatically responds to support arguments.
"""

from typing import Dict, Set
from .base_agent import BaseAgent
from coordination.message_bus import MessageBus, MessageType
from coordination.agent_registry import AgentRegistry, AgentRole
from coordination.role_policy import RolePolicyEngine
from coordination.claims import Claim, ClaimStatus, EvidenceStrength


class CriticAgent(BaseAgent):
    """Argues against factors, identifying weaknesses. Reacts to support arguments automatically."""
    
    def __init__(
        self,
        message_bus: MessageBus,
        llm_client,
        registry: AgentRegistry = None,
        policy_engine: RolePolicyEngine = None,
        resolution_tracker=None
    ):
        super().__init__(
            name="CriticAgent",
            agent_id="critic_001",
            role=AgentRole.CRITIC,
            message_bus=message_bus,
            llm_client=llm_client,
            registry=registry,
            policy_engine=policy_engine
        )
        self.claims: Dict[int, Claim] = {}  # Track critique claims per factor
        self.current_input_text: str = ""
        self.resolution_tracker = resolution_tracker
    
    def _get_input_types(self) -> Set[str]:
        return {MessageType.SUPPORT_ARGUMENT.value}
    
    def _get_output_types(self) -> Set[str]:
        return {MessageType.CRITIQUE.value}
    
    def _get_description(self) -> str:
        return "Challenges factors and support arguments; identifies flaws and analytically rejects invalid claims"
    
    def _setup_subscriptions(self):
        """Subscribe to support arguments and rebuttals - react automatically."""
        self.message_bus.subscribe(MessageType.SUPPORT_ARGUMENT.value, self._on_support_argument)
        self.message_bus.subscribe(MessageType.REBUTTAL.value, self._on_rebuttal)
    
    async def _on_support_argument(self, message: Dict):
        """React to a support argument - generate critique automatically."""
        # Skip if we already handled this
        message_id = message.get('id')
        if message_id and self.message_bus.is_handled_by(message_id, self.agent_id):
            return
        
        factor_id = message.get('factor_id')
        if not factor_id:
            return
        
        # Get factor and input text
        factor = self.message_bus.get_factor(factor_id)
        if not factor:
            return
        
        input_text = self.current_input_text or message.get('input_text_preview', '')
        
        # Generate critique
        await self.critique_factor(factor, message, input_text)
        
        # Mark as handled
        if message_id:
            self.message_bus.mark_handled(message_id, self.agent_id)
    
    async def _on_rebuttal(self, message: Dict):
        """React to a rebuttal - re-evaluate the factor if rebuttal is strong."""
        # Skip if we already handled this
        message_id = message.get('id')
        if message_id and self.message_bus.is_handled_by(message_id, self.agent_id):
            return
        
        factor_id = message.get('factor_id')
        if not factor_id:
            return
        
        # Check if this is a concession (no need to re-evaluate)
        if message.get('is_concession', False):
            return  # Concession means factor stays rejected
        
        # Get factor and input text
        factor = self.message_bus.get_factor(factor_id)
        if not factor:
            return
        
        input_text = self.current_input_text or message.get('input_text_preview', '')
        
        # Get the rebuttal content
        rebuttal_text = message.get('rebuttal', '')
        
        # Check if rebuttal is strong enough to warrant re-evaluation
        # Strong rebuttal = provides new evidence or addresses the critique directly
        is_strong_rebuttal = (
            len(rebuttal_text) > 50 and  # Substantial response
            not message.get('is_concession', False) and  # Not a concession
            ('evidence' in rebuttal_text.lower() or 
             'document' in rebuttal_text.lower() or
             'quote' in rebuttal_text.lower() or
             len(rebuttal_text) > 150)  # Detailed response
        )
        
        if is_strong_rebuttal:
            # Re-evaluate the factor with the rebuttal context
            await self.re_evaluate_after_rebuttal(factor, message, input_text)
        
        # Mark as handled
        if message_id:
            self.message_bus.mark_handled(message_id, self.agent_id)
    
    async def critique_factor(self, factor: Dict, support_argument: Dict, input_text: str) -> Dict:
        """Generate critique for a factor and its support argument. Creates structured Claim."""
        self.current_input_text = input_text
        
        # Detect context size for mode selection
        context_size = len(input_text.strip())
        is_small_context = context_size < 500
        
        # Extract supporting agent's claim if available
        support_claim_data = support_argument.get('claim')
        has_evidence = support_argument.get('has_evidence', True)
        
        # Check if factor has validation issues
        factor_validation = factor.get('validation', {})
        is_circular = factor_validation.get('is_circular', False)
        is_grounded = factor_validation.get('is_grounded', True)
        
        # Check if supporting agent conceded in any rebuttal
        has_concession = False
        all_messages = self.message_bus.get_all_messages()
        for msg in all_messages:
            if (msg.get('type') == MessageType.REBUTTAL.value and 
                msg.get('factor_id') == factor['id'] and
                msg.get('is_concession', False)):
                has_concession = True
                break
        
        # Check if this is a simple descriptive fact (before LLM call)
        context_size = len(input_text.strip())
        is_small_context = context_size < 500
        
        factor_desc = factor.get('description', '').lower()
        factor_name = factor.get('name', '').lower()
        
        # Detect if factor makes causal claim
        causal_keywords = ['caused', 'led to', 'resulted in', 'because', 'due to', 'therefore', 'thus', 'consequently']
        is_causal_claim = any(keyword in factor_desc or keyword in factor_name for keyword in causal_keywords)
        
        # Build context-aware prompt
        if is_small_context:
            mode_instruction = """CONTEXT MODE: SMALL/TRIVIAL STATEMENT
- You may use general knowledge and common sense for evaluation
- The statement is too brief for deep documentary analysis
- Apply logical reasoning and well-established facts
- CRITICAL: Do NOT hallucinate or invent counter-facts
- If using general knowledge, state it explicitly: "Based on general knowledge..."
- Still prefer document-based critique when possible"""
        else:
            mode_instruction = """CONTEXT MODE: SUBSTANTIAL DOCUMENT
- You MUST critique using ONLY information from the document
- Do NOT use external knowledge or assumptions
- Every critique must reference document content
- CRITICAL: Do NOT hallucinate or add information not in the document"""
        
        prompt = f"""You are the Opposition Counsel in Project AETHER. Your role is to present COUNTER-ARGUMENTS to the factor, not to validate it.

{mode_instruction}

=== YOUR ROLE: DEBATE OPPONENT ===

You are NOT a validator checking authenticity.
You are a DEBATE OPPONENT presenting the other side of the argument.

**Your job:**
1. Present arguments AGAINST this factor's importance or validity
2. Highlight alternative explanations or perspectives
3. Point out potential weaknesses, biases, or missing context
4. Challenge the conclusions drawn from this factor

**You should argue:**
- "This factor may not be as significant because..."
- "An alternative explanation could be..."
- "This overlooks the fact that..."
- "The evidence doesn't necessarily support this conclusion because..."

Factor:
ID: {factor['id']}
Name: {factor['name']}
Description: {factor['description']}
Validation: {'CIRCULAR - REJECT' if is_circular else 'UNGROUNDED - REJECT' if not is_grounded else 'Valid'}

Supporting Counsel's Argument:
{support_argument.get('argument', 'No argument')[:500]}
Evidence: {'NO - REJECT' if not has_evidence else 'YES'}

Document (first 1000 chars):
{input_text[:1000]}

=== REQUIRED FORMAT ===

Provide EXACTLY 2 BULLET POINTS presenting counter-arguments:

• [First counter-argument with specific reasoning]
• [Second counter-argument with alternative perspective]

RESOLUTION: [ACCEPTED | REJECTED | PARTIALLY_ACCEPTED]
JUSTIFICATION: [One sentence explaining your position]

CRITICAL RULES:
- Use bullet points (•) for each counter-argument
- EXACTLY 2 bullets - no more, no less
- Each bullet: 1-2 sentences maximum
- Present OPPOSING ARGUMENTS, not validation checks
- Challenge INTERPRETATION and SIGNIFICANCE
- Offer alternative perspectives
- Be a debate opponent, not a fact-checker
- Only REJECT if truly invalid (circular/ungrounded/contradicts document)
- Otherwise, present counter-arguments but may still PARTIALLY_ACCEPT or ACCEPT with reservations
"""

        response = await self.llm_client.generate(prompt)
        
        # Auto-accept descriptive facts in small contexts (skip debate)
        if not is_causal_claim and is_small_context and not (has_concession or is_circular or not is_grounded):
            resolution_str = "ACCEPTED"
            justification = "Descriptive fact from document - accepted without substantive debate"
        # Auto-reject ONLY for validation failures or concession (NOT for weak evidence)
        # This allows LLM to evaluate debates even when evidence is weak
        elif has_concession or is_circular or not is_grounded:
            resolution_str = "REJECTED"
            if has_concession:
                justification = "Supporting agent conceded - unable to provide documentary evidence"
            elif is_circular:
                justification = f"Circular reasoning detected: {factor_validation.get('circular_note', 'Outcome used as cause')} - REJECTED for causal inference"
            elif not is_grounded:
                justification = f"Factor not grounded in document: {factor_validation.get('grounding_note', 'No evidence in text')}"
            else:
                justification = "Factor failed validation"
        else:
            # Parse resolution from response
            import re
            resolution_match = re.search(r'RESOLUTION:\s*(ACCEPTED(?:\s*\(DESCRIPTIVE ONLY\))?|PARTIALLY_ACCEPTED|REJECTED)', response, re.IGNORECASE)
            justification_match = re.search(r'JUSTIFICATION:\s*(.+?)(?:SUB-CLAIMS:|$)', response, re.DOTALL | re.IGNORECASE)
            
            # Determine resolution
            if resolution_match:
                resolution_str = resolution_match.group(1).upper()
                # Normalize "ACCEPTED (DESCRIPTIVE ONLY)" to just "ACCEPTED" with note
                if "DESCRIPTIVE" in resolution_str:
                    resolution_str = "ACCEPTED"
                    is_descriptive_only = True
                else:
                    is_descriptive_only = False
            else:
                # Fallback: determine from keywords
                if "ANALYTICALLY REJECTED" in response.upper() or "INVALID" in response.upper() or "REJECT" in response.upper():
                    resolution_str = "REJECTED"
                elif "PARTIALLY" in response.upper() or "SOME" in response.upper():
                    resolution_str = "PARTIALLY_ACCEPTED"
                elif "ACCEPT" in response.upper():
                    resolution_str = "ACCEPTED"
                else:
                    resolution_str = "REJECTED"  # Default to rejection if unclear
                is_descriptive_only = False
            
            justification = justification_match.group(1).strip() if justification_match else "See critique above"
            
            # CRITICAL: Check if rebuttal addressed causality challenge
            # If critic raised causality issue and rebuttal only re-quoted, auto-reject
            if "CAUSAL" in response.upper() or "CAUSALITY" in response.upper():
                # Check if there's a rebuttal
                rebuttal_msg = None
                for msg in all_messages:
                    if (msg.get('type') == MessageType.REBUTTAL.value and 
                        msg.get('factor_id') == factor['id']):
                        rebuttal_msg = msg
                        break
                
                if rebuttal_msg:
                    rebuttal_text = rebuttal_msg.get('rebuttal', '').upper()
                    # Check if rebuttal only re-quotes without addressing causality
                    has_causal_mechanism = any(term in rebuttal_text for term in [
                        'MECHANISM', 'BECAUSE', 'THEREFORE', 'THUS', 'CONSEQUENTLY',
                        'LEADS TO', 'RESULTS IN', 'CAUSES'
                    ])
                    
                    if not has_causal_mechanism and 'QUOTE:' in rebuttal_text:
                        # Rebuttal only re-quoted without addressing causality - Critic wins
                        resolution_str = "REJECTED"
                        justification = "Critic raised causality challenge - rebuttal only re-quoted document without providing causal mechanism"
            
            # Add descriptive-only note if applicable
            if is_descriptive_only and resolution_str == "ACCEPTED":
                justification = f"DESCRIPTIVE ONLY: {justification}. This factor describes what happened but does NOT establish causality."
        
        # Parse sub-claims for PARTIALLY_ACCEPTED
        sub_claims = []
        if resolution_str == "PARTIALLY_ACCEPTED":
            subclaims_match = re.search(r'SUB-CLAIMS:(.*?)(?:$)', response, re.DOTALL | re.IGNORECASE)
            if subclaims_match:
                subclaims_text = subclaims_match.group(1)
                subclaim_lines = re.findall(r'-\s*(.+?):\s*(ACCEPTED|REJECTED)', subclaims_text, re.IGNORECASE)
                sub_claims = [
                    {"claim": claim.strip(), "status": status.upper()}
                    for claim, status in subclaim_lines
                ]
        
        # Parse sub-claims if PARTIALLY_ACCEPTED
        sub_claims = []
        if "PARTIALLY_ACCEPTED" in resolution_str:
            # Extract bullet points from response to create sub-claims
            lines = response.split('\n')
            bullet_points = [line.strip() for line in lines if line.strip().startswith('•')]
            
            if len(bullet_points) >= 2:
                # First bullet is typically the accepted part, second is the concern
                sub_claims = [
                    {
                        "claim": bullet_points[0].replace('•', '').strip()[:100],
                        "status": "ACCEPTED",
                        "justification": "Valid counter-argument acknowledged"
                    },
                    {
                        "claim": bullet_points[1].replace('•', '').strip()[:100] if len(bullet_points) > 1 else "Additional concerns noted",
                        "status": "NEEDS_CLARIFICATION",
                        "justification": "Requires further evidence or clarification"
                    }
                ]
            else:
                # Fallback: create generic sub-claims
                sub_claims = [
                    {
                        "claim": "Core argument has merit",
                        "status": "ACCEPTED",
                        "justification": "Partially valid based on available evidence"
                    },
                    {
                        "claim": "Some aspects require clarification",
                        "status": "NEEDS_CLARIFICATION",
                        "justification": "Additional evidence or context needed"
                    }
                ]
        
        # CRITICAL: Validate resolution exists and is valid
        allowed_resolutions = ["ACCEPTED", "PARTIALLY_ACCEPTED", "REJECTED"]
        if resolution_str not in allowed_resolutions:
            # Force to REJECTED if invalid
            resolution_str = "REJECTED"
            justification = f"Invalid resolution detected - defaulting to REJECTED. Original: {resolution_str}"
        
        # Track resolution
        if self.resolution_tracker:
            from validation.resolution_tracker import ResolutionStatus
            status_map = {
                "ACCEPTED": ResolutionStatus.ACCEPTED,
                "PARTIALLY_ACCEPTED": ResolutionStatus.PARTIALLY_ACCEPTED,
                "REJECTED": ResolutionStatus.REJECTED
            }
            self.resolution_tracker.set_resolution(
                factor_id=factor['id'],
                status=status_map[resolution_str],
                justification=justification,
                sub_claims=sub_claims if sub_claims else None,
                critic_agent_id=self.agent_id
            )
        
        # Create structured claim
        factor_id = factor['id']
        claim = Claim(
            claim_id=f"critique_{factor_id}_{self._get_timestamp()}",
            content=response,
            factor_id=factor_id,
            agent_id=self.agent_id
        )
        
        # Determine claim status based on resolution
        if resolution_str == "REJECTED":
            claim.status = ClaimStatus.INVALIDATED
            claim.confidence = 0.9
        elif resolution_str == "PARTIALLY_ACCEPTED":
            claim.status = ClaimStatus.WEAKENED
            claim.confidence = 0.5
        else:  # ACCEPTED
            claim.status = ClaimStatus.CHALLENGED
            claim.confidence = 0.7
        
        # Link to supporting agent's claim if available
        if support_claim_data:
            support_claim_id = support_claim_data.get('claim_id')
            if support_claim_id:
                claim.challenges.append(support_claim_id)
        
        self.claims[factor_id] = claim
        
        critique = {
            "type": MessageType.CRITIQUE.value,
            "factor_id": factor['id'],
            "factor_name": factor['name'],
            "responding_to": support_argument.get('agent_id', 'SupportingAgent'),
            "argument": response,
            "claim": claim.to_dict(),
            "resolution": resolution_str,
            "justification": justification,
            "sub_claims": sub_claims,
            "verdict": resolution_str,  # Keep for backward compatibility
            "timestamp": self._get_timestamp()
        }
        
        await self._publish(critique)
        return critique
    
    async def re_evaluate_after_rebuttal(self, factor: Dict, rebuttal_message: Dict, input_text: str) -> Dict:
        """Re-evaluate a factor after receiving a strong rebuttal."""
        factor_id = factor['id']
        rebuttal_text = rebuttal_message.get('rebuttal', '')
        
        # Get original critique
        original_critique = None
        all_messages = self.message_bus.get_all_messages()
        for msg in all_messages:
            if (msg.get('type') == MessageType.CRITIQUE.value and 
                msg.get('factor_id') == factor_id):
                original_critique = msg.get('argument', '')
                break
        
        # Build re-evaluation prompt
        prompt = f"""You are the Critic Agent re-evaluating a factor after receiving a rebuttal.

Factor:
ID: {factor['id']}
Name: {factor['name']}
Description: {factor['description']}

Your Original Critique:
{original_critique[:500] if original_critique else 'N/A'}

Supporting Agent's Rebuttal:
{rebuttal_text}

Document (first 1000 chars):
{input_text[:1000]}

=== YOUR TASK ===

The Supporting Agent has provided a rebuttal. Re-evaluate your critique:

1. **Did the rebuttal provide NEW evidence?** (document quotes, specific references)
2. **Did the rebuttal address your concerns?** (directly respond to your critique)
3. **Should you change your decision?**

=== REQUIRED FORMAT (100 words max) ===

REBUTTAL ASSESSMENT:
[2-3 sentences: Did the rebuttal provide sufficient new evidence or reasoning?]

UPDATED RESOLUTION: [ACCEPTED | PARTIALLY_ACCEPTED | REJECTED | MAINTAIN_ORIGINAL]
JUSTIFICATION: [One sentence explaining why]

CRITICAL RULES:
- If rebuttal provides NEW documentary evidence → Consider ACCEPTED or PARTIALLY_ACCEPTED
- If rebuttal just repeats claims without evidence → MAINTAIN_ORIGINAL (keep rejected)
- If rebuttal addresses your critique with quotes → Consider changing decision
- Be fair: if they provided what you asked for, accept it
- Maximum 100 words!
"""
        
        response = await self.llm_client.generate(prompt)
        
        # Parse the updated resolution
        updated_resolution = "MAINTAIN_ORIGINAL"
        justification = "No change after rebuttal"
        
        if "UPDATED RESOLUTION:" in response:
            resolution_line = response.split("UPDATED RESOLUTION:")[1].split("\n")[0].strip()
            if "ACCEPTED" in resolution_line and "PARTIALLY" not in resolution_line:
                updated_resolution = "ACCEPTED"
            elif "PARTIALLY_ACCEPTED" in resolution_line:
                updated_resolution = "PARTIALLY_ACCEPTED"
            elif "REJECTED" in resolution_line:
                updated_resolution = "REJECTED"
        
        if "JUSTIFICATION:" in response:
            justification = response.split("JUSTIFICATION:")[1].split("\n")[0].strip()
        
        # Only publish if resolution changed
        if updated_resolution != "MAINTAIN_ORIGINAL":
            critique_update = {
                "type": MessageType.CRITIQUE.value,
                "factor_id": factor_id,
                "agent_id": self.agent_id,
                "argument": f"[UPDATED AFTER REBUTTAL] {response[:300]}",
                "verdict": updated_resolution,
                "justification": justification,
                "is_update": True,
                "timestamp": self._get_timestamp()
            }
            
            await self._publish(critique_update)
            
            print(f"✓ Critic re-evaluated factor {factor_id}: {updated_resolution}")
            print(f"  Reason: {justification}")
        else:
            print(f"○ Critic maintains original decision for factor {factor_id}")
        
        return {
            "updated_resolution": updated_resolution,
            "justification": justification
        }
