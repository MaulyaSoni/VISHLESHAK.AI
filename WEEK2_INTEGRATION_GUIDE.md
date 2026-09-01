# Week 2 Integration Guide for data_agent_3.py

## Overview
This document shows exactly where to add 3 code blocks to integrate the reasoning engine into `backend/scripts/data_agent_3.py`.

---

## Addition 1: Import Reasoning Engine

**Location**: Top of file, after existing imports (around line 1-50)

**Add this code**:
```python
# Week 2: Reasoning Engine Integration
try:
    from reasoning_engine import plan_task, reflect_on_result, summarize_progress, inject_plan_into_messages
    REASONING_AVAILABLE = True
    print("✅ Reasoning engine loaded")
except ImportError as e:
    REASONING_AVAILABLE = False
    print(f"⚠️  Reasoning engine not available: {e}")
```

---

## Addition 2: Add Planning Step at Start of run_agent()

**Location**: Inside `run_agent()` function, after creating `state` and `messages` variables, BEFORE the ReAct loop starts

**Find this section** (search for `state = {` in run_agent):
```python
def run_agent(instruction: str, force_task_type: str = None) -> dict:
    # ... existing setup code ...
    
    state = {
        'done': False,
        'steps_taken': [],
        'errors': [],
        'warnings': [],
        # ... other state fields ...
    }
    
    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': instruction}
    ]
    
    # <<< ADD PLANNING CODE HERE >>>
```

**Add this code AFTER state and messages are created**:
```python
    # Week 2: Generate execution plan
    plan = {}
    if REASONING_AVAILABLE:
        print('  📋 Planning execution...')
        
        # Get data summary if available
        data_summary = ''
        if state.get('dataset_path'):
            try:
                import pandas as pd
                df = pd.read_csv(state['dataset_path'])
                data_summary = f"Dataset: {len(df)} rows, {len(df.columns)} columns. Columns: {', '.join(df.columns.tolist())}"
            except:
                pass
        
        # Generate plan
        plan = plan_task(instruction, data_summary, client, MODEL_INSIGHT)
        
        if plan.get('task_summary'):
            print(f"  Plan: {plan['task_summary']}")
            for s in plan.get('steps', []):
                print(f"    Step {s['step_id']}: [{s['tool']}] {s['goal']}")
        
        # Inject plan into messages
        messages = inject_plan_into_messages(messages, plan, state)
```

---

## Addition 3: Add Reflection After Each Tool Call

**Location**: Inside the ReAct loop, AFTER the `dispatch()` call and BEFORE appending result to messages

**Find this section** (search for the ReAct loop - it looks like):
```python
    # ReAct Loop
    while not state['done'] and iteration < max_iterations:
        # ... get LLM response ...
        # ... parse tool call ...
        
        # Execute tool
        name = tool_call.get('name')
        args = tool_call.get('args', {})
        result = dispatch(name, args, state)
        
        # <<< ADD REFLECTION CODE HERE >>>
        
        # Append to messages
        messages.append({
            'role': 'assistant',
            'content': ...
        })
```

**Add this code AFTER `result = dispatch(...)` and BEFORE `messages.append(...)`**:
```python
        # Week 2: Reflect on result quality
        if REASONING_AVAILABLE and not state['done']:
            # Find the goal for this step from plan
            step_goal = next(
                (s['goal'] for s in plan.get('steps', []) if s['tool'] == name),
                f'Execute {name} successfully'
            )
            
            # Evaluate result
            reflection = reflect_on_result(step_goal, result, client, MODEL_SUPER)
            score = reflection.get('score', 3)
            
            if score < 3 and reflection.get('correction'):
                # Inject correction hint
                correction = reflection['correction']
                result += f'\n\nREFLECTION (score {score}/5): {reflection["issue"]}. Try: {correction}'
                print(f'  ⚠️  Reflection score: {score}/5 — injecting correction hint')
            elif score >= 4:
                print(f'  ✅ Reflection score: {score}/5')
```

---

## Testing the Integration

After making these 3 additions:

1. **Test basic functionality**:
   ```python
   python -c "from backend.scripts.data_agent_3 import run_agent; print('Import OK')"
   ```

2. **Run a simple analysis**:
   ```python
   from backend.scripts.data_agent_3 import run_agent
   result = run_agent("Analyze this dataset and find key insights", force_task_type='analysis_only')
   print(result)
   ```

3. **Check logs for reasoning output**:
   You should see:
   ```
   ✅ Reasoning engine loaded
   📋 Planning execution...
   Plan: Analyze the dataset and generate insights
     Step 1: [load_csv] Load the dataset
     Step 2: [run_eda] Perform exploratory analysis
     ...
   ✅ Reflection score: 4/5
   ```

---

## Important Notes

1. **Backwards Compatible**: If reasoning_engine.py is not available, `REASONING_AVAILABLE = False` and agent runs normally without planning/reflection

2. **No Breaking Changes**: The 3 additions are purely additive - they don't modify existing logic

3. **Performance**: Planning adds ~2-3 seconds at start, reflection adds ~1 second per tool call (uses fast 8B model)

4. **Fallback Plan**: If LLM planning fails, a minimal 3-step fallback plan is used automatically

---

## What This Achieves

✅ **Intelligent Planning**: Agent creates structured execution plan before starting  
✅ **Quality Control**: Each tool result is evaluated for quality  
✅ **Self-Correction**: Low-quality results get correction hints injected  
✅ **Progress Tracking**: Clear visibility into what's done and what's next  
✅ **Graceful Degradation**: Works even if reasoning engine unavailable  
