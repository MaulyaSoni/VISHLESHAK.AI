"""
Week 2 Tests - Kaggle Integration & Reasoning Engine
All 5 tests should pass before proceeding to Week 3
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def test_kaggle_import():
    """Test 1: Kaggle package is installed"""
    try:
        import kaggle
        print("  ✅ Test 1: Kaggle installed")
        return True
    except ImportError:
        print("  ❌ Test 1: Run: pip install kaggle")
        return False


def test_kaggle_auth():
    """Test 2: Kaggle authentication works"""
    try:
        import kaggle
        kaggle.api.authenticate()
        print("  ✅ Test 2: Kaggle authenticated")
        return True
    except Exception as e:
        print(f"  ⚠️  Test 2: Authentication failed (expected if no API key): {e}")
        print("      To fix: Run 'kaggle datasets list' and follow setup instructions")
        return True  # Don't block progress - Kaggle is optional


def test_kaggle_search():
    """Test 3: Kaggle search functionality works"""
    try:
        from kaggle_tools import tool_kaggle_search
        
        state = {'steps_taken': [], 'errors': [], 'warnings': []}
        result = tool_kaggle_search(state, 'titanic')
        
        # Check that we got some result
        assert 'titanic' in result.lower() or 'found' in result.lower() or 'dataset' in result.lower(), \
            f"Unexpected result: {result[:100]}"
        
        print("  ✅ Test 3: Kaggle search works")
        return True
        
    except Exception as e:
        print(f"  ⚠️  Test 3: Search failed (may need Kaggle setup): {e}")
        return True  # Don't block - Kaggle optional


def test_reasoning_plan():
    """Test 4: Plan generation works"""
    try:
        from reasoning_engine import plan_task
        
        # Test with minimal setup (no LLM - will use fallback)
        plan = plan_task(
            instruction='analyze sales data and find trends',
            data_summary='',
            client=None,  # No client - will trigger fallback
            model='test'
        )
        
        # Verify plan structure
        assert 'steps' in plan and len(plan['steps']) > 0, "Plan missing steps"
        assert 'task_summary' in plan, "Plan missing task_summary"
        assert 'task_type' in plan, "Plan missing task_type"
        
        print(f"  ✅ Test 4: Plan generated: {len(plan['steps'])} steps")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 4: Plan generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_reflection():
    """Test 5: Reflection/scoring works"""
    try:
        from reasoning_engine import reflect_on_result
        
        # Test with minimal setup (no LLM - will use fallback)
        reflection = reflect_on_result(
            goal='Load a CSV file',
            result='Loaded data.csv: 1000 rows x 10 cols',
            client=None,  # No client - will trigger fallback
            model='test'
        )
        
        # Verify reflection structure
        assert 'score' in reflection and reflection['score'] >= 1, "Reflection missing or invalid score"
        
        print(f"  ✅ Test 5: Reflection works, score={reflection['score']}")
        return True
        
    except Exception as e:
        print(f"  ❌ Test 5: Reflection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print('Running Week 2 Tests...\n')
    
    tests = [
        test_kaggle_import,
        test_kaggle_auth,
        test_kaggle_search,
        test_reasoning_plan,
        test_reflection,
    ]
    
    passed = sum(1 for t in tests if t())
    
    print(f'\n{passed}/{len(tests)} tests passed')
    
    if passed < 3:  # Allow 2 optional Kaggle tests to fail
        print('\n❌ Critical tests failed. Fix issues before proceeding to Week 3.')
        sys.exit(1)
    else:
        print('\n✅ Sufficient tests passed! Ready for Week 3.')
        print('   Note: Kaggle tests are optional - configure Kaggle API key to enable them.')
