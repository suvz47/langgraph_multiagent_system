class AgenticMemory:
    def __init__(self):
        self.memory = {}

    def save(self, agent_name, info):
        if agent_name not in self.memory:
            self.memory[agent_name] = []
        self.memory[agent_name].append(info)

    def retrieve(self, agent_name):
        return self.memory.get(agent_name, []) 