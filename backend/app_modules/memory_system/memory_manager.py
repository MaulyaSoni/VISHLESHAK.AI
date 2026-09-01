from backend.app_modules.memory_system.episodic_store import build_episodic_context, save_analysis_memory
from backend.app_modules.memory_system.context_persistence import build_context_prompt, auto_update_from_analysis

class MemoryManager:
    def __init__(self, user_id: str):
        self.user_id = user_id

    def load_context_for_agent(self, state: dict) -> str:
        ep = build_episodic_context(self.user_id, state)
        sm = build_context_prompt(self.user_id)
        
        c = []
        if sm: c.append(sm)
        if ep: c.append(ep)
        return "\n\n".join(c)

    def save_after_analysis(self, state: dict):
        save_analysis_memory(self.user_id, state)
        auto_update_from_analysis(self.user_id, state)

_mem_managers = {}
def get_memory_manager(user_id='default') -> MemoryManager:
    if user_id not in _mem_managers:
        _mem_managers[user_id] = MemoryManager(user_id)
    return _mem_managers[user_id]
