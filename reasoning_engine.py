"""
Vishleshak AI — Advanced Reasoning Engine
Provides: task planning, result reflection, progress tracking.
Uses Groq LLM for intelligent reasoning.
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# PLAN GENERATION
# ─────────────────────────────────────────────────────────────────────────────

PLAN_SYSTEM_PROMPT = """You are an expert data science planning assistant. Given a user instruction and optional data summary, create a step-by-step execution plan.

Available tools:
- kaggle_search: Search Kaggle for datasets
- kaggle_download: Download a Kaggle dataset
- load_csv: Load a CSV file into pandas
- preprocess: Handle missing values, encode categoricals, scale numerics
- run_eda: Exploratory data analysis (distributions, correlations, insights)
- plan_charts: Plan visualization strategy
- generate_charts: Create Plotly charts
- generate_insights: Generate AI-powered insights
- detect_target: Identify target variable for ML
- train_model: Train ML model (classification or regression)
- evaluate_model: Evaluate model performance
- compile_report: Generate final analysis report

Rules:
1. Each step must use exactly ONE tool
2. Steps must be in logical execution order
3. Keep plans concise (5-10 steps max)
4. Skip ML steps if instruction doesn't mention prediction/modeling
5. Always end with compile_report

Return JSON with this exact structure:
{
  "task_summary": "Brief 1-sentence summary of what will be done",
  "task_type": "analysis_only" | "analysis_ml" | "analysis_ml_notebook",
  "steps": [
    {
      "step_id": 1,
      "tool": "tool_name",
      "goal": "What this step should accomplish",
      "expected_output": "What success looks like"
    }
  ]
}"""


def plan_task(
    instruction: str,
    data_summary: str,
    client,
    model: str = "llama-3.3-70b-versatile"
) -> Dict[str, Any]:
    """
    Generate an execution plan for the data analysis task.
    
    Args:
        instruction: User's analysis instruction
        data_summary: Brief summary of available data (can be empty)
        client: Groq LLM client
        model: Model name to use
    
    Returns:
        dict with task_summary, task_type, and steps array
    """
    try:
        user_message = f"INSTRUCTION: {instruction}\n\n"
        if data_summary:
            user_message += f"DATA SUMMARY: {data_summary}\n\n"
        user_message += "Create a detailed execution plan."
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": PLAN_SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON (might be wrapped in code blocks)
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        plan = json.loads(response_text.strip())
        
        # Validate structure
        if 'steps' not in plan or not isinstance(plan['steps'], list):
            raise ValueError("Plan missing 'steps' array")
        
        print(f"  📋 Plan generated: {len(plan['steps'])} steps")
        return plan
        
    except Exception as e:
        print(f"  ⚠️  Plan generation failed: {e}")
        # Return minimal fallback plan
        return {
            "task_summary": "Analyze the dataset",
            "task_type": "analysis_only",
            "steps": [
                {
                    "step_id": 1,
                    "tool": "load_csv",
                    "goal": "Load the dataset",
                    "expected_output": "Data loaded successfully"
                },
                {
                    "step_id": 2,
                    "tool": "run_eda",
                    "goal": "Perform exploratory analysis",
                    "expected_output": "EDA insights generated"
                },
                {
                    "step_id": 3,
                    "tool": "compile_report",
                    "goal": "Generate final report",
                    "expected_output": "Report compiled"
                }
            ]
        }


# ─────────────────────────────────────────────────────────────────────────────
# RESULT REFLECTION
# ─────────────────────────────────────────────────────────────────────────────

REFLECTION_SYSTEM_PROMPT = """You are a quality assurance assistant for data science workflows. Evaluate the result of a tool execution.

Score from 1-5:
1 = Complete failure, wrong output, error
2 = Major issues, missing key information
3 = Acceptable but could be better
4 = Good, minor improvements possible
5 = Excellent, exceeds expectations

For scores < 3, provide a specific correction suggestion.

Return JSON:
{
  "score": 1-5,
  "issue": "Brief description of any problems",
  "correction": "Specific suggestion to improve (only if score < 3)",
  "strengths": "What was done well"
}"""


def reflect_on_result(
    goal: str,
    result: str,
    client,
    model: str = "llama-3.1-8b-instant"
) -> Dict[str, Any]:
    """
    Evaluate the quality of a tool execution result.
    
    Args:
        goal: What the step was trying to achieve
        result: Actual result from tool execution
        client: Groq LLM client
        model: Model name (use faster/cheaper model for reflection)
    
    Returns:
        dict with score, issue, correction (if needed), strengths
    """
    try:
        # Truncate result if too long (reflection doesn't need full output)
        result_truncated = result[:2000] if len(result) > 2000 else result
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"GOAL: {goal}\n\nRESULT: {result_truncated}\n\nEvaluate this result."}
            ],
            temperature=0.2,
            max_tokens=300
        )
        
        # Parse response
        response_text = response.choices[0].message.content.strip()
        
        # Extract JSON
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        
        reflection = json.loads(response_text.strip())
        
        # Validate
        if 'score' not in reflection:
            raise ValueError("Reflection missing 'score'")
        
        return reflection
        
    except Exception as e:
        print(f"  ⚠️  Reflection failed: {e}")
        # Return neutral reflection on failure
        return {
            "score": 3,
            "issue": "Could not evaluate result",
            "correction": None,
            "strengths": "Result generated"
        }


# ─────────────────────────────────────────────────────────────────────────────
# PROGRESS SUMMARIZATION
# ─────────────────────────────────────────────────────────────────────────────

def summarize_progress(state: dict, plan: dict) -> str:
    """
    Create a human-readable progress summary.
    
    Args:
        state: Agent state dict with steps_taken, errors, warnings
        plan: Execution plan with steps array
    
    Returns:
        Formatted progress string
    """
    if not plan.get('steps'):
        return "No plan available"
    
    total_steps = len(plan['steps'])
    completed = len(state.get('steps_taken', []))
    errors = len(state.get('errors', []))
    warnings = len(state.get('warnings', []))
    
    # Determine which steps are done
    step_names_done = set()
    for step in state.get('steps_taken', []):
        # Extract tool name from step (format: "tool_name: details")
        if ':' in step:
            tool_name = step.split(':')[0].strip()
            step_names_done.add(tool_name)
    
    # Build progress lines
    progress_lines = []
    progress_lines.append(f"Progress: {completed}/{total_steps} steps completed")
    
    if errors > 0:
        progress_lines.append(f"Errors: {errors}")
    if warnings > 0:
        progress_lines.append(f"Warnings: {warnings}")
    
    progress_lines.append("\nStep Status:")
    for step in plan['steps']:
        tool = step.get('tool', 'unknown')
        status = '✅' if tool in step_names_done else '⏳'
        progress_lines.append(f"  {status} Step {step['step_id']}: [{tool}] {step['goal']}")
    
    return '\n'.join(progress_lines)


# ─────────────────────────────────────────────────────────────────────────────
# MESSAGE INJECTION
# ─────────────────────────────────────────────────────────────────────────────

def inject_plan_into_messages(messages: list, plan: dict, state: dict) -> list:
    """
    Add plan summary and progress to message history so agent stays on track.
    
    Args:
        messages: Current message history
        plan: Execution plan
        state: Agent state
    
    Returns:
        Updated messages list with plan injected
    """
    if not plan.get('steps'):
        return messages
    
    # Format steps as readable list
    steps_text = '\n'.join(
        f"  Step {s['step_id']}: [{s['tool']}] — {s['goal']}"
        for s in plan.get('steps', [])
    )
    
    # Get current progress
    progress = summarize_progress(state, plan)
    
    # Create system reminder
    system_reminder = f'''TASK PLAN (follow this order):
{steps_text}

CURRENT STATUS: {progress}

Execute the next uncompleted step. When all steps are done, call compile_report.'''
    
    # Inject as a new system message after the original system message
    for i, msg in enumerate(messages):
        if msg.get('role') == 'system':
            new_messages = messages[:i+1] + [
                {'role': 'system', 'content': system_reminder}
            ] + messages[i+1:]
            return new_messages
    
    # If no system message found, append to end
    return messages + [{'role': 'system', 'content': system_reminder}]
