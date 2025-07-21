from typing import Dict

def intake_node(state: Dict) -> Dict:
    claim = state.get('claim', {})
    state.setdefault('agent_messages', []).append('IntakeAgent: Received claim.')
    # Simulate triage, e.g., extract claim type
    state['scenario'] = claim.get('type', 'unknown')
    return state 