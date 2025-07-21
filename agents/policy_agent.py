from typing import Dict
from llm.groq_llm import GroqLLM

def policy_node(state: Dict, llm: GroqLLM) -> Dict:
    claim = state.get('claim', {})
    policy_id = claim.get('policy_id', 'unknown')
    # Simulate policy lookup
    policy = {'policy_id': policy_id, 'coverage': 'full', 'status': 'active'}
    # Use LLM to summarize/validate policy
    summary = llm.chat([
        {"role": "system", "content": "You are an expert insurance policy analyst."},
        {"role": "user", "content": f"Summarize and validate this policy for claim: {policy}"}
    ])
    state['policy'] = policy
    state['policy_llm_summary'] = summary
    state.setdefault('agent_messages', []).append(f'PolicyAgent: Looked up and summarized policy {policy_id}.')
    return state 