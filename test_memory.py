import os
import sqlite3
import pandas as pd
from backend.app_modules.memory_system.episodic_store import save_analysis_memory, recall_recent, DB_PATH
from backend.app_modules.memory_system.context_persistence import save_context, load_context, PROFILE_DIR

def setup_module(module):
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(PROFILE_DIR / 'test_user.json'):
        os.remove(PROFILE_DIR / 'test_user.json')

def test_save_and_recall_analysis():
    df = pd.DataFrame({'a': [1,2], 'b': [2,3]})
    state = {'dataset': df, 'user_query': 'Test Q', 'analysis_result': {'executive_summary': 'Success'}}
    save_analysis_memory('test_user', state)
    
    analyses = recall_recent('test_user')
    assert len(analyses) == 1
    assert analyses[0]['instruction'] == 'Test Q'

def test_context_persistence_load_default():
    ctx = load_context('new_user')
    assert ctx['business_profile']['sector'] == 'general'
    assert 'kpi_history' in ctx

def test_context_persistence_save_load():
    ctx = load_context('test_user')
    ctx['business_profile']['sector'] = 'insurance'
    save_context('test_user', ctx)
    
    ctx2 = load_context('test_user')
    assert ctx2['business_profile']['sector'] == 'insurance'

def test_memory_manager_integration():
    from backend.app_modules.memory_system.memory_manager import get_memory_manager
    mm = get_memory_manager('test_mm_user')
    df = pd.DataFrame({'claim': [1], 'premium': [2]})
    state = {'dataset': df, 'user_query': 'Analyze claims', 'domain_context': {'sector': 'insurance'}, 'domain_kpis': {'loss_ratio': 0.5}}
    mm.save_after_analysis(state)
    
    ctx = mm.load_context_for_agent({'dataset': df})
    assert 'Analyze claims' in ctx

def test_episodic_context():
    from backend.app_modules.memory_system.episodic_store import build_episodic_context
    df = pd.DataFrame({'a': [1]})
    state = {'dataset': df, 'user_query': 'Analysis 1', 'analysis_result': {'executive_summary': 'Findings 1'}}
    save_analysis_memory('test_user_2', state)
    
    ctx = build_episodic_context('test_user_2', {'dataset': df})
    assert 'Analysis 1' in ctx
