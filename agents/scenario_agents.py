from typing import Dict
from llm.groq_llm import GroqLLM

def auto_scenario_node(state: Dict, llm: GroqLLM) -> Dict:
    # Use LLM to decide if more info is needed or to process claim
    decision = llm.chat([
        {"role": "system", "content": "You are an expert auto insurance claim adjuster."},
        {"role": "user", "content": f"Given this claim and docs: {state.get('claim')} {state.get('llm_summaries', [])}. Should more documents be requested? Reply 'yes' or 'no' and explain."}
    ])
    state.setdefault('agent_messages', []).append(f'AutoInsuranceAgent: LLM decision: {decision}')
    if 'yes' in decision.lower():
        state['needs_more_docs'] = True
        state['result'] = 'Auto claim needs more documents.'
    else:
        state['needs_more_docs'] = False
        state['result'] = 'Auto claim processed.'
    return state

def health_scenario_node(state: Dict, llm: GroqLLM) -> Dict:
    decision = llm.chat([
        {"role": "system", "content": "You are an expert health insurance claim adjuster."},
        {"role": "user", "content": f"Given this claim and docs: {state.get('claim')} {state.get('llm_summaries', [])}. Should more documents be requested? Reply 'yes' or 'no' and explain."}
    ])
    state.setdefault('agent_messages', []).append(f'HealthInsuranceAgent: LLM decision: {decision}')
    if 'yes' in decision.lower():
        state['needs_more_docs'] = True
        state['result'] = 'Health claim needs more documents.'
    else:
        state['needs_more_docs'] = False
        state['result'] = 'Health claim processed.'
    return state

def property_scenario_node(state: Dict, llm: GroqLLM) -> Dict:
    decision = llm.chat([
        {"role": "system", "content": "You are an expert property insurance claim adjuster."},
        {"role": "user", "content": f"Given this claim and docs: {state.get('claim')} {state.get('llm_summaries', [])}. Should more documents be requested? Reply 'yes' or 'no' and explain."}
    ])
    state.setdefault('agent_messages', []).append(f'PropertyInsuranceAgent: LLM decision: {decision}')
    if 'yes' in decision.lower():
        state['needs_more_docs'] = True
        state['result'] = 'Property claim needs more documents.'
    else:
        state['needs_more_docs'] = False
        state['result'] = 'Property claim processed.'
    return state 