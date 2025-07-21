from typing import Dict

def coordinator_router_node(state: Dict) -> Dict:
    state.setdefault('agent_messages', []).append('Coordinator: Routing to scenario agent.')
    return state

def coordinator_router_edge(state: Dict) -> str:
    scenario = state.get('scenario', 'unknown')
    if scenario == 'auto':
        return 'auto_scenario_node'
    elif scenario == 'health':
        return 'health_scenario_node'
    elif scenario == 'property':
        return 'property_scenario_node'
    else:
        return 'end' 