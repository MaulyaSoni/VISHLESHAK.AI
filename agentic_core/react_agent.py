"""
Vishleshak ReAct Agent
Main agentic reasoning engine with Thought → Action → Observation loop
"""

import logging
import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

_AGENT_AVAILABLE = False
AgentExecutor = None
create_react_agent = None

try:
    from langchain.agents import AgentExecutor, create_react_agent
    _AGENT_AVAILABLE = True
except ImportError:
    try:
        from langchain.agents import create_react_agent
        from langchain_core.agents import AgentExecutor
        _AGENT_AVAILABLE = True
    except ImportError:
        logger.warning("AgentExecutor not available - using fallback mode")

from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

from core.llm import get_chat_llm
try:
    from config import agent_config
    SMART_TOOL_SELECTION = agent_config.SMART_TOOL_SELECTION
    MAX_ITERATIONS = agent_config.MAX_ITERATIONS
    MAX_EXECUTION_TIME = agent_config.MAX_EXECUTION_TIME
    ENABLE_REFLECTION = agent_config.ENABLE_REFLECTION
    MIN_CONFIDENCE_THRESHOLD = agent_config.MIN_CONFIDENCE_THRESHOLD
    MAX_REFLECTION_RETRIES = agent_config.MAX_REFLECTION_RETRIES
    ENABLE_FALLBACK = True
except Exception:
    SMART_TOOL_SELECTION = True
    MAX_ITERATIONS = 15
    MAX_EXECUTION_TIME = 120
    ENABLE_REFLECTION = True
    MIN_CONFIDENCE_THRESHOLD = 0.7
    MAX_REFLECTION_RETRIES = 2
    ENABLE_FALLBACK = True

try:
    from .agent_memory import get_agent_memory
except ImportError:
    get_agent_memory = lambda: None

try:
    from .tool_selector import ToolSelector
except ImportError:
    class ToolSelector:
        def select_tools(self, question, available_tools):
            return available_tools[:3]

try:
    from .reflection_layer import ReflectionLayer
except ImportError:
    class ReflectionLayer:
        def reflect(self, **kwargs):
            return {"confidence": 80, "suggestions": []}

try:
    from .prompts.system_prompt import SYSTEM_PROMPT, REACT_SYSTEM
except ImportError:
    REACT_SYSTEM = "You are a data analysis agent."

try:
    from .prompts.react_prompt import REACT_INSTRUCTION
except ImportError:
    REACT_INSTRUCTION = "Answer the user's question step by step."


class VishleshakReActAgent:
    """
    Advanced ReAct agent for Vishleshak AI
    """
    
    def __init__(
        self,
        tools: List[BaseTool],
        data_context: Optional[str] = None,
        user_id: str = "default",
        verbose: bool = True,
    ):
        self.tools = tools
        self.data_context = data_context or "No dataset loaded"
        self.user_id = user_id
        self.verbose = verbose
        
        try:
            self.memory = get_agent_memory()
        except:
            self.memory = None
        
        try:
            self.tool_selector = ToolSelector()
        except:
            self.tool_selector = None
            
        try:
            self.reflection_layer = ReflectionLayer() if agent_config.ENABLE_REFLECTION else None
        except:
            self.reflection_layer = None
            
        self.iteration_count = 0
        self.tool_calls = []
        self.thoughts = []
        
        if _AGENT_AVAILABLE and create_react_agent is not None:
            try:
                self.agent = self._build_agent()
                logger.info(f"✅ Vishleshak ReAct Agent initialized with {len(tools)} tools")
            except Exception as e:
                logger.warning(f"Failed to build agent: {e}")
                self.agent = None
        else:
            self.agent = None
            logger.info("⚠️ Agentic mode unavailable - using fallback")
    
    def _build_agent(self):
        if not _AGENT_AVAILABLE or create_react_agent is None:
            return None
            
        tool_names = ", ".join([t.name for t in self.tools])
        system_msg = REACT_SYSTEM.format(
            max_iterations=agent_config.MAX_ITERATIONS,
            tool_names=tool_names,
        )
        prompt = PromptTemplate(
            template=system_msg + "\n\n" + REACT_INSTRUCTION,
            input_variables=["input", "agent_scratchpad"],
        )
        
        try:
            agent = create_react_agent(
                llm=get_chat_llm(),
                tools=self.tools,
                prompt=prompt,
            )
            
            if AgentExecutor is not None:
                executor = AgentExecutor(
                    agent=agent,
                    tools=self.tools,
                    verbose=self.verbose,
                    max_iterations=agent_config.MAX_ITERATIONS,
                    max_execution_time=agent_config.MAX_EXECUTION_TIME,
                    handle_parsing_errors=True,
                    return_intermediate_steps=True,
                )
                return executor
            return agent
        except Exception as e:
            logger.error(f"Error building agent: {e}")
            return None
    
    def run(
        self,
        question: str,
        context: Optional[Dict] = None,
        callbacks: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        logger.info(f"🤖 Agent processing: {question[:80]}...")
        start_time = datetime.now()
        self.iteration_count = 0
        self.tool_calls = []
        self.thoughts = []
        
        if self.agent is None:
            return self._fallback_response(question)
        
        try:
            if self.tool_selector and agent_config.SMART_TOOL_SELECTION:
                try:
                    selected_tools = self.tool_selector.select_tools(
                        question=question,
                        available_tools=self.tools,
                    )
                    self.agent.tools = selected_tools
                    logger.info(f"🎯 Selected {len(selected_tools)} tools")
                except:
                    pass
            
            invoke_kwargs = {
                "input": self._format_input(question),
            }
            
            if self.data_context:
                invoke_kwargs["data_context"] = self.data_context
            
            config = {}
            if callbacks:
                config["callbacks"] = callbacks

            result = self.agent.invoke(invoke_kwargs, config=config)
            answer = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            reasoning_trace = self._extract_reasoning(intermediate_steps)
            confidence = 1.0
            reflection_result = None
            
            if self.reflection_layer and agent_config.ENABLE_REFLECTION:
                try:
                    reflection_result = self.reflection_layer.reflect(
                        question=question,
                        answer=answer,
                        context=self.data_context,
                        reasoning_trace=reasoning_trace,
                    )
                    confidence = reflection_result["confidence"] / 100
                except:
                    pass
            
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Agent completed in {execution_time:.1f}s (confidence: {confidence:.2%})")
            return {
                "answer": answer,
                "reasoning_trace": reasoning_trace,
                "tools_used": self.tool_calls,
                "thoughts": self.thoughts,
                "confidence": confidence,
                "execution_time": execution_time,
                "reflection": reflection_result,
                "iterations": self.iteration_count,
            }
        except Exception as e:
            logger.error(f"❌ Agent error: {e}", exc_info=True)
            if agent_config.ENABLE_FALLBACK:
                logger.info("🔄 Falling back to simple response")
                return self._fallback_response(question)
            raise
    
    def _format_input(self, question: str) -> str:
        if self.data_context and self.data_context != "No dataset loaded":
            return f"Dataset context: {self.data_context}\n\nQuestion: {question}"
        return question
    
    def _extract_reasoning(self, intermediate_steps: List[Tuple]) -> List[Dict]:
        trace = []
        for step in intermediate_steps:
            try:
                action, observation = step
                thought = ""
                if hasattr(action, "log"):
                    match = re.search(r"Thought:\s*(.+?)(?:\n|$)", action.log)
                    if match:
                        thought = match.group(1).strip()
                tool_name = action.tool if hasattr(action, "tool") else "unknown"
                tool_input = action.tool_input if hasattr(action, "tool_input") else {}
                trace.append({
                    "thought": thought,
                    "action": tool_name,
                    "action_input": tool_input,
                    "observation": str(observation)[:500],
                })
                self.tool_calls.append(tool_name)
                if thought:
                    self.thoughts.append(thought)
                self.iteration_count += 1
            except:
                continue
        return trace
    
    def _classify_question(self, question: str) -> str:
        q_lower = question.lower()
        if any(k in q_lower for k in ["trend", "over time", "change"]):
            return "trend"
        elif any(k in q_lower for k in ["correlat", "relationship"]):
            return "correlation"
        elif any(k in q_lower for k in ["outlier", "anomaly", "unusual"]):
            return "anomaly"
        elif any(k in q_lower for k in ["predict", "forecast", "future"]):
            return "forecast"
        elif any(k in q_lower for k in ["chart", "plot", "visualize"]):
            return "visualization"
        elif any(k in q_lower for k in ["mean", "average", "distribution"]):
            return "statistical"
        else:
            return "general"
    
    def _fallback_response(self, question: str) -> Dict[str, Any]:
        logger.info("Using fallback response mode")
        try:
            from chatbot.qa_chain import EnhancedQAChain
            fallback_answer = f"I encountered difficulty with the agentic approach. Here's a direct analysis:\n\n[Fallback response - integrate with existing QA chain]"
            return {
                "answer": fallback_answer,
                "reasoning_trace": [],
                "tools_used": [],
                "thoughts": ["Fallback mode activated"],
                "confidence": 0.5,
                "execution_time": 0.0,
                "reflection": None,
                "iterations": 0,
                "fallback": True,
            }
        except Exception as e:
            logger.error(f"Fallback also failed: {e}")
            return {
                "answer": "I apologize, but I encountered an error processing your question. Please try rephrasing or simplifying your query.",
                "error": str(e),
                "fallback": True,
            }


def create_vishleshak_agent(tools: List[BaseTool], data_context: Optional[str] = None, **kwargs) -> VishleshakReActAgent:
    return VishleshakReActAgent(tools=tools, data_context=data_context, **kwargs)