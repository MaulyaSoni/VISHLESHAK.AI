# Vishleshak AI - React + Flask Migration

## Overview
Complete migration from Streamlit UI to React 18 + Flask API architecture.

## Architecture
```
React (port 5173) ←→ Flask API (port 5000) ←→ Python Backend (unchanged)
```

## Project Structure

### Flask API (`flask_api/`)
```
flask_api/
├── __init__.py              # Flask app factory
├── app.py                   # Entry point
├── socket_handlers.py       # Socket.IO for proactive flags
└── routes/
    ├── auth_routes.py       # /api/auth/*
    ├── analysis_routes.py   # /api/analysis/*
    ├── file_routes.py       # /api/files/*
    ├── memory_routes.py     # /api/memory/*
    └── report_routes.py     # /api/reports/*
```

### React Frontend (`frontend/`)
```
frontend/
├── package.json             # Dependencies
├── vite.config.ts           # Vite config with proxy
├── tailwind.config.ts       # Design tokens
├── index.html
└── src/
    ├── main.tsx             # Entry point
    ├── App.tsx              # Router + auth guard
    ├── index.css            # Global styles
    ├── store/
    │   ├── useAppStore.ts   # Zustand: user, domain, dataset
    │   └── useAgentStore.ts # Zustand: agent trace, charts, flags
    ├── api/
    │   ├── client.ts        # Axios instance
    │   ├── auth.ts          # Auth hooks
    │   ├── files.ts         # File upload/scan hooks
    │   └── analysis.ts      # Analysis + SSE streaming
    ├── components/
    │   ├── layout/
    │   │   ├── AppShell.tsx # Main layout
    │   │   ├── Sidebar.tsx  # Dataset list, domain selector
    │   │   └── TopBar.tsx   # Status, user badge
    │   ├── analysis/
    │   │   ├── ChatPane.tsx      # Chat + trace
    │   │   └── DashboardPane.tsx # Charts + stats
    │   └── filemanager/
    │       └── FileManagerPanel.tsx # Upload/scan modal
    └── pages/
        ├── LoginPage.tsx
        ├── WorkspacePage.tsx
        └── SettingsPage.tsx
```

## Setup Instructions

### 1. Install Flask API Dependencies
```bash
cd d:\FINBOT-2\VISHLESHAK_AI
pip install flask flask-cors flask-socketio flask-login python-dotenv
```

### 2. Start Flask API
```bash
python flask_api/app.py
```
API will be available at `http://localhost:5000`

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 4. Start React Dev Server
```bash
npm run dev
```
Frontend will be available at `http://localhost:5173`

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Get current user

### Files
- `POST /api/files/upload` - Upload dataset
- `POST /api/files/scan` - Scan folder
- `POST /api/files/load-path` - Load file by path

### Analysis
- `POST /api/analysis/run` - Start analysis
- `GET /api/analysis/stream` - SSE stream results

### Memory
- `GET /api/memory/stats` - Get memory stats
- `DELETE /api/memory/dataset/:hash` - Clear dataset memory
- `DELETE /api/memory/all` - Clear all memory

### Reports
- `GET /api/reports/list` - List reports
- `GET /api/reports/download/:filename` - Download PDF

## Socket.IO Events

### Client → Server
- `connect` - Authenticate and join user room
- `join` - Join session room

### Server → Client
- `proactive_flag` - Push notification
- `connected` - Connection confirmed

## Design System

### Colors
- `bg-base`: #0A0B0F (page background)
- `bg-surface`: #111318 (cards)
- `bg-elevated`: #1A1D24 (inputs)
- `border-subtle`: #23262F
- `text-primary`: #F0F2F5
- `text-muted`: #6B7280
- `accent-blue`: #4F8EF7

### Domain Colors
- Finance: primary #1A3A5C, accent #2E86AB
- Insurance: primary #1A4A2E, accent #2EAB6E
- General: primary #2A1A4A, accent #7B4EAB

## Features Implemented

✅ Flask API with all routes
✅ React + Vite + TypeScript setup
✅ Tailwind CSS with design tokens
✅ Zustand state management
✅ React Query API hooks
✅ SSE streaming for agent trace
✅ Socket.IO for proactive flags
✅ File upload with react-dropzone
✅ Dark theme UI
✅ Responsive layout
✅ Login/Workspace/Settings pages

## Next Steps

1. Install dependencies and test
2. Connect to existing Python backend
3. Add Plotly chart rendering
4. Implement PDF report generation
5. Add more statistical visualizations
