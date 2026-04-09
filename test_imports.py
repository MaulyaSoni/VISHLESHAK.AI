try:
    from langchain_core.agents import create_react_agent, AgentExecutor
    print('langchain_core.agents: OK')
except Exception as e:
    print(f'langchain_core.agents: FAIL - {e}')

try:
    from langchain.agents import AgentExecutor
    print('langchain.agents.AgentExecutor: OK')
except Exception as e:
    print(f'langchain.agents.AgentExecutor: FAIL - {e}')

try:
    from langchain.agents import create_react_agent
    print('langchain.agents.create_react_agent: OK')
except Exception as e:
    print(f'langchain.agents.create_react_agent: FAIL - {e}')

print()
print('Checking installed packages:')
import importlib.metadata
for pkg in ['langchain', 'langchain-core', 'langchain-community']:
    try:
        ver = importlib.metadata.version(pkg)
        print(f'{pkg}: {ver}')
    except:
        print(f'{pkg}: NOT INSTALLED')