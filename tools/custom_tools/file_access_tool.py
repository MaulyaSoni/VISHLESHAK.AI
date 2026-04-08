"""
Vishleshak v2 — File Access Tool
==================================
Handles all local dataset loading for the supervisor pipeline.

Two modes:
  1. Streamlit file_uploader  → user drags/drops file in UI
  2. Local path input         → user types absolute path or folder path

Supports: .csv, .xlsx, .xls, .json
Saves to:  data/uploads/<user_id>/<filename> for session isolation
"""

import os
import io
import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Union, Tuple

import pandas as pd

logger = logging.getLogger("vishleshak.file_access")

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json"}
MAX_FILE_SIZE_MB = 200
UPLOAD_BASE_DIR = "data/uploads"


def _load_csv(source: Union[str, io.BytesIO]) -> pd.DataFrame:
    """Load CSV with encoding fallback chain."""
    for enc in ["utf-8", "latin-1", "cp1252", "utf-8-sig"]:
        try:
            if isinstance(source, str):
                return pd.read_csv(source, encoding=enc, low_memory=False)
            else:
                source.seek(0)
                return pd.read_csv(source, encoding=enc, low_memory=False)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise ValueError(f"CSV load failed: {e}")
    raise ValueError("Could not decode CSV with any supported encoding.")


def _load_excel(source: Union[str, io.BytesIO]) -> pd.DataFrame:
    """Load Excel — first sheet by default."""
    if isinstance(source, io.BytesIO):
        source.seek(0)
    xl = pd.ExcelFile(source)
    if len(xl.sheet_names) > 1:
        logger.info(f"Multiple sheets found: {xl.sheet_names}. Loading first: '{xl.sheet_names[0]}'")
    return pd.read_excel(source, sheet_name=xl.sheet_names[0])


def _load_json(source: Union[str, io.BytesIO]) -> pd.DataFrame:
    """Load JSON — handles list-of-dicts, nested dict, and records key."""
    if isinstance(source, str):
        with open(source, "r", encoding="utf-8") as f:
            raw = json.load(f)
    else:
        source.seek(0)
        raw = json.load(source)

    if isinstance(raw, list):
        return pd.DataFrame(raw)
    elif isinstance(raw, dict):
        for key in ("data", "records", "rows", "items", "results"):
            if key in raw and isinstance(raw[key], list):
                return pd.DataFrame(raw[key])
        return pd.json_normalize(raw)
    else:
        raise ValueError(f"Unsupported JSON root type: {type(raw)}")


def _read_file(path_or_buffer: Union[str, io.BytesIO], ext: str) -> pd.DataFrame:
    """Dispatch to correct loader by extension."""
    ext = ext.lower()
    if ext == ".csv":
        return _load_csv(path_or_buffer)
    elif ext in (".xlsx", ".xls"):
        return _load_excel(path_or_buffer)
    elif ext == ".json":
        return _load_json(path_or_buffer)
    else:
        raise ValueError(f"Unsupported extension: {ext}. Use .csv, .xlsx, .xls, .json")


def _build_file_meta(df: pd.DataFrame, filename: str, source_path: str = "") -> dict:
    """Build lightweight file metadata."""
    col_types = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            col_types[col] = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            col_types[col] = "datetime"
        else:
            col_types[col] = "categorical"

    col_hash = hashlib.md5(",".join(sorted(df.columns.tolist())).encode()).hexdigest()[:12]

    return {
        "filename": filename,
        "source_path": source_path,
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "columns": df.columns.tolist(),
        "col_types": col_types,
        "dataset_hash": col_hash,
        "size_mb": round(df.memory_usage(deep=True).sum() / 1e6, 2),
        "loaded_at": datetime.now().isoformat(),
        "null_total": int(df.isnull().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
    }


def _save_to_uploads(df: pd.DataFrame, filename: str, user_id: str) -> str:
    """Persist loaded DataFrame as CSV to data/uploads/<user_id>/."""
    user_dir = os.path.join(UPLOAD_BASE_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)

    safe_name = "".join(c if c.isalnum() or c in ("_", ".", "-") else "_" for c in filename)
    save_path = os.path.join(user_dir, safe_name)
    df.to_csv(save_path, index=False, encoding="utf-8")
    logger.info(f"Dataset saved to {save_path}")
    return save_path


def load_from_upload(uploaded_file, user_id: str = "default") -> Tuple[pd.DataFrame, dict]:
    """Load from Streamlit UploadedFile object."""
    filename = uploaded_file.name
    ext = Path(filename).suffix.lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

    uploaded_file.seek(0, 2)
    size_mb = uploaded_file.tell() / 1e6
    uploaded_file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f}MB. Max: {MAX_FILE_SIZE_MB}MB")

    buffer = io.BytesIO(uploaded_file.read())
    df = _read_file(buffer, ext)
    meta = _build_file_meta(df, filename)
    _save_to_uploads(df, filename, user_id)

    logger.info(f"[upload] Loaded '{filename}' -> {df.shape[0]}r x {df.shape[1]}c for user={user_id}")
    return df, meta


def load_from_path(file_path: str, user_id: str = "default") -> Tuple[pd.DataFrame, dict]:
    """Load from an absolute or relative local file path."""
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}. Use load_from_folder() for directories.")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {SUPPORTED_EXTENSIONS}")

    size_mb = path.stat().st_size / 1e6
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large: {size_mb:.1f}MB. Max: {MAX_FILE_SIZE_MB}MB")

    df = _read_file(str(path), ext)
    meta = _build_file_meta(df, path.name, source_path=str(path))
    _save_to_uploads(df, path.name, user_id)

    logger.info(f"[path] Loaded '{path.name}' -> {df.shape[0]}r x {df.shape[1]}c for user={user_id}")
    return df, meta


def scan_folder(folder_path: str) -> list:
    """List all supported dataset files in a folder."""
    folder = Path(folder_path).expanduser().resolve()

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")
    if not folder.is_dir():
        raise ValueError(f"Not a directory: {folder}")

    files = []
    for f in sorted(folder.iterdir()):
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            size_mb = round(f.stat().st_size / 1e6, 2)
            files.append({
                "name": f.name,
                "path": str(f),
                "ext": f.suffix.lower(),
                "size_mb": size_mb,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })

    if not files:
        raise FileNotFoundError(
            f"No supported dataset files found in: {folder}"
        )

    logger.info(f"[folder] Found {len(files)} dataset(s) in {folder}")
    return files


def load_from_folder(folder_path: str, filename: Optional[str] = None,
                     user_id: str = "default") -> Tuple[pd.DataFrame, dict]:
    """Scan folder and load a specific file or the largest file."""
    files = scan_folder(folder_path)

    if filename:
        match = next((f for f in files if f["name"] == filename), None)
        if not match:
            available = [f["name"] for f in files]
            raise FileNotFoundError(f"'{filename}' not found. Available: {available}")
        selected = match
    else:
        selected = max(files, key=lambda f: f["size_mb"])
        logger.info(f"[folder] Auto-selected largest: {selected['name']} ({selected['size_mb']}MB)")

    return load_from_path(selected["path"], user_id=user_id)


def load_dataset(source, mode: str = "auto", user_id: str = "default",
                 filename: Optional[str] = None) -> Tuple[pd.DataFrame, dict]:
    """Unified entry point — auto-detects mode or accepts explicit mode."""
    if mode == "auto":
        if hasattr(source, "read") and hasattr(source, "name"):
            mode = "upload"
        elif isinstance(source, str):
            p = Path(source).expanduser().resolve()
            mode = "folder" if p.is_dir() else "path"
        else:
            raise ValueError(f"Cannot auto-detect mode for source type: {type(source)}")

    if mode == "upload":
        return load_from_upload(source, user_id=user_id)
    elif mode == "path":
        return load_from_path(str(source), user_id=user_id)
    elif mode == "folder":
        return load_from_folder(str(source), filename=filename, user_id=user_id)
    else:
        raise ValueError(f"Unknown mode: '{mode}'. Use 'upload', 'path', or 'folder'.")


def render_file_loader(user_id: str):
    """Streamlit UI component for file loading."""
    try:
        import streamlit as st
    except ImportError:
        return None, None

    from tools.custom_tools.file_access_tool import (
        load_dataset, scan_folder, SUPPORTED_EXTENSIONS
    )

    st.subheader("Load Dataset")

    tab_upload, tab_path, tab_folder = st.tabs(["Upload File", "File Path", "Folder"])

    df_return = None
    meta_return = None

    with tab_upload:
        uploaded = st.file_uploader(
            "Drag & drop or browse",
            type=["csv", "xlsx", "xls", "json"],
            help=f"Max {MAX_FILE_SIZE_MB}MB"
        )
        if uploaded and st.button("Load", key="btn_upload"):
            with st.spinner("Loading..."):
                try:
                    df, meta = load_dataset(uploaded, mode="upload", user_id=user_id)
                    st.success(f"Loaded **{meta['filename']}** — {meta['rows']:,} rows x {meta['cols']} cols")
                    df_return, meta_return = df, meta
                except Exception as e:
                    st.error(str(e))

    with tab_path:
        path_input = st.text_input(
            "Absolute file path",
            placeholder="/home/user/sales_data.csv"
        )
        if path_input and st.button("Load", key="btn_path"):
            with st.spinner("Loading..."):
                try:
                    df, meta = load_dataset(path_input, mode="path", user_id=user_id)
                    st.success(f"Loaded **{meta['filename']}** — {meta['rows']:,} rows x {meta['cols']} cols")
                    df_return, meta_return = df, meta
                except Exception as e:
                    st.error(str(e))

    with tab_folder:
        folder_input = st.text_input(
            "Folder path",
            placeholder="/home/user/datasets/"
        )
        if folder_input:
            try:
                files = scan_folder(folder_input)
                file_names = [f"{f['name']} ({f['size_mb']}MB)" for f in files]
                choice_idx = st.selectbox("Select dataset", range(len(file_names)),
                                          format_func=lambda i: file_names[i])
                if st.button("Load Selected", key="btn_folder"):
                    with st.spinner("Loading..."):
                        selected = files[choice_idx]
                        df, meta = load_dataset(selected["path"], mode="path", user_id=user_id)
                        st.success(f"Loaded **{meta['filename']}** — {meta['rows']:,} rows x {meta['cols']} cols")
                        df_return, meta_return = df, meta
            except Exception as e:
                st.error(str(e))

    return df_return, meta_return