"""
Vishleshak AI — Kaggle Integration Tools
Provides 4 agent tools: search, download, list_competitions, submit.
Requires: pip install kaggle + ~/.kaggle/kaggle.json
"""
import os
import json
import shutil
import zipfile
import traceback
from pathlib import Path
from typing import Optional

KAGGLE_DATA_DIR = Path('./kaggle_data')
KAGGLE_DATA_DIR.mkdir(exist_ok=True)


def _ensure_kaggle():
    """Check kaggle is configured. Returns (api, None) or (None, error_msg)."""
    try:
        import kaggle
        # Set credentials from env if not in kaggle.json
        if os.getenv('KAGGLE_USERNAME'):
            os.environ['KAGGLE_USERNAME'] = os.getenv('KAGGLE_USERNAME')
            os.environ['KAGGLE_KEY'] = os.getenv('KAGGLE_KEY', '')
        kaggle.api.authenticate()
        return kaggle.api, None
    except Exception as e:
        return None, f'Kaggle not configured: {e}. Run: kaggle datasets list'


def tool_kaggle_search(state: dict, query: str) -> str:
    """
    Search Kaggle for datasets matching the query.
    
    Args:
        state: Agent state dict (tracks steps_taken, errors, warnings)
        query: Search query (e.g., 'titanic survival', 'house prices')
    
    Returns:
        Formatted string with top 10 dataset results
    """
    api, error = _ensure_kaggle()
    if error:
        state['errors'].append(error)
        return f'KAGGLE_SEARCH_FAILED: {error}'
    
    try:
        datasets = api.datasets_list(search=query, sort_by='hottest', size=10)
        
        if not datasets:
            return f'No datasets found for query: "{query}"'
        
        results = []
        for ds in datasets[:10]:
            results.append({
                'slug': ds.ref,
                'title': ds.title,
                'description': ds.description[:200] if ds.description else '',
                'votes': int(ds.totalVotes) if hasattr(ds, 'totalVotes') else 0,
                'downloads': int(ds.totalDownloads) if hasattr(ds, 'totalDownloads') else 0,
            })
        
        # Format output for agent
        output_lines = [f'Found {len(results)} datasets for "{query}":\n']
        for i, ds in enumerate(results, 1):
            output_lines.append(
                f"{i}. **{ds['slug']}**\n"
                f"   Title: {ds['title']}\n"
                f"   Votes: {ds['votes']} | Downloads: {ds['downloads']}\n"
                f"   Description: {ds['description']}\n"
            )
        
        result_text = '\n'.join(output_lines)
        state['steps_taken'].append(f'kaggle_search: found {len(results)} datasets')
        return result_text
        
    except Exception as e:
        error_msg = f'KAGGLE_SEARCH_ERROR: {e}'
        state['errors'].append(error_msg)
        return error_msg


def tool_kaggle_download(state: dict, dataset_slug: str) -> str:
    """
    Download a Kaggle dataset to ./kaggle_data/.
    
    Args:
        state: Agent state dict
        dataset_slug: Dataset identifier (e.g., 'titanic', 'impliedo/titanic')
    
    Returns:
        Path to downloaded dataset and file listing
    """
    api, error = _ensure_kaggle()
    if error:
        state['errors'].append(error)
        return f'KAGGLE_DOWNLOAD_FAILED: {error}'
    
    try:
        # Create download directory
        download_dir = KAGGLE_DATA_DIR / dataset_slug.replace('/', '_')
        download_dir.mkdir(parents=True, exist_ok=True)
        
        # Download dataset
        print(f"  Downloading {dataset_slug} to {download_dir}...")
        api.dataset_download_files(dataset_slug, path=str(download_dir), unzip=True)
        
        # List downloaded files
        files = list(download_dir.rglob('*'))
        files = [f for f in files if f.is_file()]
        
        # Find CSV files
        csv_files = [f for f in files if f.suffix.lower() == '.csv']
        
        result_lines = [
            f'Downloaded dataset: {dataset_slug}',
            f'Directory: {download_dir}',
            f'Files: {len(files)}',
            f'CSV files: {len(csv_files)}',
        ]
        
        if csv_files:
            result_lines.append('\nCSV files available:')
            for csv in csv_files:
                size_kb = csv.stat().st_size / 1024
                result_lines.append(f'  - {csv.name} ({size_kb:.1f} KB)')
            result_lines.append(f'\nPrimary dataset: {csv_files[0].name}')
            result_lines.append(f'Full path: {csv_files[0]}')
        else:
            result_lines.append('\nNo CSV files found. Available files:')
            for f in files[:10]:
                result_lines.append(f'  - {f.name}')
        
        result_text = '\n'.join(result_lines)
        state['steps_taken'].append(f'kaggle_download: {dataset_slug} -> {download_dir}')
        state['dataset_path'] = str(csv_files[0]) if csv_files else None
        
        return result_text
        
    except Exception as e:
        error_msg = f'KAGGLE_DOWNLOAD_ERROR: {e}'
        state['errors'].append(error_msg)
        return error_msg


def tool_kaggle_competitions(state: dict) -> str:
    """
    List active Kaggle competitions.
    
    Args:
        state: Agent state dict
    
    Returns:
        Formatted string with top 10 active competitions
    """
    api, error = _ensure_kaggle()
    if error:
        state['errors'].append(error)
        return f'KAGGLE_COMPETITIONS_FAILED: {error}'
    
    try:
        competitions = api.competitions_list(status='active', page=1)
        
        if not competitions:
            return 'No active competitions found.'
        
        results = []
        for comp in competitions[:10]:
            results.append({
                'slug': comp.ref,
                'title': comp.title,
                'url': comp.url,
                'deadline': str(comp.deadline) if hasattr(comp, 'deadline') else 'N/A',
                'reward': comp.reward if hasattr(comp, 'reward') else 'N/A',
                'teamSize': comp.teamCount if hasattr(comp, 'teamCount') else 'N/A',
            })
        
        output_lines = ['Active Kaggle Competitions:\n']
        for i, comp in enumerate(results, 1):
            output_lines.append(
                f"{i}. **{comp['slug']}**\n"
                f"   Title: {comp['title']}\n"
                f"   Deadline: {comp['deadline']}\n"
                f"   Reward: {comp['reward']}\n"
                f"   Teams: {comp['teamSize']}\n"
                f"   URL: https://kaggle.com{comp['url']}\n"
            )
        
        result_text = '\n'.join(output_lines)
        state['steps_taken'].append('kaggle_competitions: listed 10 active competitions')
        return result_text
        
    except Exception as e:
        error_msg = f'KAGGLE_COMPETITIONS_ERROR: {e}'
        state['errors'].append(error_msg)
        return error_msg


def tool_kaggle_submit(state: dict, file_path: str, competition: str) -> str:
    """
    Submit a prediction file to a Kaggle competition.
    
    Args:
        state: Agent state dict
        file_path: Path to submission CSV file
        competition: Competition slug (e.g., 'titanic')
    
    Returns:
        Submission status
    """
    api, error = _ensure_kaggle()
    if error:
        state['errors'].append(error)
        return f'KAGGLE_SUBMIT_FAILED: {error}'
    
    try:
        # Verify file exists
        if not os.path.exists(file_path):
            return f'KAGGLE_SUBMIT_FAILED: File not found: {file_path}'
        
        # Submit to competition
        print(f"  Submitting to {competition}...")
        api.competition_submit(
            file_name=file_path,
            message='Submission from Vishleshak AI Agent',
            competition=competition
        )
        
        result_text = f'Successfully submitted {file_path} to {competition}'
        state['steps_taken'].append(f'kaggle_submit: {file_path} -> {competition}')
        return result_text
        
    except Exception as e:
        error_msg = f'KAGGLE_SUBMIT_ERROR: {e}'
        state['errors'].append(error_msg)
        return error_msg
