"""ReAct prompts for agent execution"""

REACT_INSTRUCTION = """Answer the user's question using the following format:

Thought: I need to understand what the user is asking
Action: tool_name
Action Input: {{"param1": "value1", "param2": "value2"}}
Observation: [tool output will appear here]

... (repeat Thought/Action/Observation cycle as needed)

Thought: I now have enough information to answer
Final Answer: [comprehensive answer based on observations]

IMPORTANT:
- Always start with "Thought:"
- Action Input must be valid JSON
- Review each Observation before continuing
- Provide detailed Final Answer with specific numbers/findings

Question: {input}

{agent_scratchpad}
"""

REACT_PARSER_INSTRUCTIONS = """Parse the agent's output:
- Extract "Thought:", "Action:", "Action Input:", and "Final Answer:" sections
- Validate JSON in Action Input
- Return structured format for execution
"""
