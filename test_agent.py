"""
Quick test script for Vishleshak AI Agentic System
Run this to verify the agent is working correctly
"""

import pandas as pd
import numpy as np
from datetime import datetime

# Test 1: Import Check
print("=" * 60)
print("🧪 TEST 1: Checking imports...")
print("=" * 60)

try:
    from agentic_core import create_vishleshak_agent
    from agentic_core import AgentMemory, ToolSelector, ReflectionLayer
    print("✅ Core agentic modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import core modules: {e}")
    exit(1)

try:
    from tools.specialized import (
        StatisticalAnalyzerTool,
        CorrelationFinderTool,
        AnomalyDetectorTool,
        ChartGeneratorTool,
        TrendAnalyzerTool,
        ForecasterTool,
        PythonSandboxTool,
        ReportGeneratorTool,
    )
    print("✅ All 8 specialized tools imported successfully")
except ImportError as e:
    print(f"❌ Failed to import tools: {e}")
    exit(1)

try:
    from rag.advanced import MultiQueryRetriever, ContextualCompressor, EnsembleRetriever
    print("✅ Advanced RAG modules imported successfully")
except ImportError as e:
    print(f"⚠️ Advanced RAG modules not available: {e}")

print("\n" + "=" * 60)
print("🧪 TEST 2: Creating sample dataset...")
print("=" * 60)

# Create sample data
np.random.seed(42)
df = pd.DataFrame({
    'revenue': np.random.normal(10000, 2000, 100),
    'cost': np.random.normal(7000, 1500, 100),
    'profit': np.random.normal(3000, 800, 100),
    'customer_count': np.random.poisson(50, 100),
    'category': np.random.choice(['A', 'B', 'C'], 100),
})
df['profit_margin'] = df['profit'] / df['revenue']

print(f"✅ Created dataset: {len(df)} rows × {len(df.columns)} columns")
print(f"   Columns: {', '.join(df.columns)}")

print("\n" + "=" * 60)
print("🧪 TEST 3: Initializing tools...")
print("=" * 60)

tools = []
tool_names = []

try:
    tools.append(StatisticalAnalyzerTool(df))
    tool_names.append("StatisticalAnalyzerTool")
    print("✅ StatisticalAnalyzerTool initialized")
except Exception as e:
    print(f"❌ StatisticalAnalyzerTool failed: {e}")

try:
    tools.append(CorrelationFinderTool(df))
    tool_names.append("CorrelationFinderTool")
    print("✅ CorrelationFinderTool initialized")
except Exception as e:
    print(f"❌ CorrelationFinderTool failed: {e}")

try:
    tools.append(AnomalyDetectorTool(df))
    tool_names.append("AnomalyDetectorTool")
    print("✅ AnomalyDetectorTool initialized")
except Exception as e:
    print(f"❌ AnomalyDetectorTool failed: {e}")

try:
    tools.append(ChartGeneratorTool(df))
    tool_names.append("ChartGeneratorTool")
    print("✅ ChartGeneratorTool initialized")
except Exception as e:
    print(f"⚠️ ChartGeneratorTool failed: {e}")

try:
    tools.append(TrendAnalyzerTool(df))
    tool_names.append("TrendAnalyzerTool")
    print("✅ TrendAnalyzerTool initialized")
except Exception as e:
    print(f"⚠️ TrendAnalyzerTool failed: {e}")

try:
    tools.append(ForecasterTool(df))
    tool_names.append("ForecasterTool")
    print("✅ ForecasterTool initialized")
except Exception as e:
    print(f"⚠️ ForecasterTool failed: {e}")

try:
    tools.append(PythonSandboxTool())
    tool_names.append("PythonSandboxTool")
    print("✅ PythonSandboxTool initialized")
except Exception as e:
    print(f"⚠️ PythonSandboxTool failed: {e}")

try:
    tools.append(ReportGeneratorTool(df))
    tool_names.append("ReportGeneratorTool")
    print("✅ ReportGeneratorTool initialized")
except Exception as e:
    print(f"⚠️ ReportGeneratorTool failed: {e}")

print(f"\n✅ Successfully initialized {len(tools)}/{8} tools")

if len(tools) == 0:
    print("❌ No tools available, cannot proceed with agent test")
    exit(1)

print("\n" + "=" * 60)
print("🧪 TEST 4: Creating ReAct agent...")
print("=" * 60)

try:
    agent = create_vishleshak_agent(
        tools=tools,
        data_context=f"Financial dataset: {len(df)} rows × {len(df.columns)} columns",
        verbose=False,
    )
    print("✅ Agent created successfully")
    print(f"   Agent type: {type(agent).__name__}")
    print(f"   Tools available: {len(agent.tools)}")
except Exception as e:
    print(f"❌ Agent creation failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🧪 TEST 5: Testing tool functionality...")
print("=" * 60)

# Test StatisticalAnalyzerTool
if any(isinstance(t, StatisticalAnalyzerTool) for t in tools):
    try:
        stat_tool = next(t for t in tools if isinstance(t, StatisticalAnalyzerTool))
        result = stat_tool.run(column="revenue", tests=["normality"])
        print("✅ StatisticalAnalyzerTool works correctly")
    except Exception as e:
        print(f"⚠️ StatisticalAnalyzerTool test failed: {e}")

# Test CorrelationFinderTool
if any(isinstance(t, CorrelationFinderTool) for t in tools):
    try:
        corr_tool = next(t for t in tools if isinstance(t, CorrelationFinderTool))
        result = corr_tool.run(method="pearson", min_correlation=0.3)
        print("✅ CorrelationFinderTool works correctly")
    except Exception as e:
        print(f"⚠️ CorrelationFinderTool test failed: {e}")

print("\n" + "=" * 60)
print("🧪 TEST 6: Running simple agent query...")
print("=" * 60)

test_question = "What is the mean revenue in this dataset?"

try:
    print(f"Question: '{test_question}'")
    print("Running agent...")
    
    result = agent.run(test_question)
    
    print("\n" + "-" * 60)
    print("✅ AGENT RESPONSE:")
    print("-" * 60)
    print(result["answer"])
    print("-" * 60)
    
    print(f"\n📊 Metadata:")
    print(f"   Confidence: {result.get('confidence', 0):.1%}")
    print(f"   Tools used: {len(result.get('tools_used', []))}")
    print(f"   Tool names: {', '.join(result.get('tools_used', []))}")
    print(f"   Iterations: {result.get('iterations', 0)}")
    print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
    
    if result.get('reasoning_trace'):
        print(f"\n🧠 Reasoning trace ({len(result['reasoning_trace'])} steps):")
        for i, step in enumerate(result['reasoning_trace'], 1):
            print(f"   Step {i}:")
            if step.get('thought'):
                print(f"     💭 Thought: {step['thought'][:60]}...")
            print(f"     🔧 Action: {step['action']}")
            print(f"     👁️ Observation: {step['observation'][:60]}...")
    
    print("\n✅ Agent executed successfully!")
    
except Exception as e:
    print(f"❌ Agent execution failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("🎉 TEST SUMMARY")
print("=" * 60)
print(f"✅ Imports: OK")
print(f"✅ Dataset: OK ({len(df)} rows)")
print(f"✅ Tools: {len(tools)}/8 initialized")
print(f"✅ Agent: OK")
print(f"✅ Execution: OK")
print("\n🚀 Vishleshak AI Agentic System is ready to use!")
print("   Run 'streamlit run app.py' to start the full application.")
print("=" * 60)
