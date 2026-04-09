import sys, os
sys.path.insert(0, '.')

print("Testing v2 components...")

# 1. Graph compiles
from agentic_core.supervisor_graph import get_supervisor_graph
sup = get_supervisor_graph()
print('Supervisor graph: OK')

# 2. File tool loads
from tools.custom_tools.file_access_tool import load_dataset
print("File access tool: OK")
print('File access tool: OK')

# 3. Memory manager initialises
from core.enhanced_memory import EnhancedMemoryManager as MemoryManager
mm = MemoryManager(user_id='smoketest')
print('Memory manager: OK')

# 4. Proactive engine starts
from agentic_core.proactive_engine import ProactiveEngine
pe = ProactiveEngine(user_id='smoketest', session_id='s0')
print('Proactive engine: OK')

# 5. PDF subgraph imports
from tools.specialized.pdf_subgraph import generate_pdf_report
print('PDF subgraph: OK')

# 6. React agent (check AgentExecutor import fix)
from agentic_core.react_agent import VishleshakReActAgent, _AGENT_AVAILABLE
print(f'React agent: OK (AgentExecutor available: {_AGENT_AVAILABLE})')

print()
print('All v2 components loaded successfully.')
