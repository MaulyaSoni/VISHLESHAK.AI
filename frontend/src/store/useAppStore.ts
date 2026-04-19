import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Domain = 'general' | 'finance' | 'insurance' | 'ecommerce'
export type AppMode = 'Analysis' | 'Q&A' | 'DataAgent'

export interface User {
  id: number
  email: string
  username: string
  domain: Domain
}

export interface Dataset {
  hash: string
  filename: string
  rows: number
  cols: number
  numericCount: number
  categoricalCount: number
  missingPct: number
  meta: Record<string, unknown>
}

export interface ChatSession {
  id: string
  title: string
  timestamp: number
}

export interface AnalysisReport {
  id: string
  title: string
  instruction: string
  mode: string
  createdAt: string
}

interface AppState {
  // User & Auth
  user: User | null
  setUser: (user: User | null) => void
  authToken: string | null
  setAuthToken: (token: string | null) => void
  
  // Mode - from app.py session_state.mode
  mode: AppMode
  setMode: (mode: AppMode) => void
  
  // Domain
  domain: Domain
  setDomain: (domain: Domain) => void
  
  // AI Engine toggle - from app.py use_agent_mode
  useAgentMode: boolean
  setUseAgentMode: (enabled: boolean) => void
  
  // Dataset - from app.py session_state.data
  currentDataset: Dataset | null
  setCurrentDataset: (dataset: Dataset | null) => void
  datasets: Dataset[]
  addDataset: (dataset: Dataset) => void
  
  // Chat History - from app.py session_state.all_sessions
  chatSessions: ChatSession[]
  addChatSession: (session: ChatSession) => void
  currentSessionId: string
  setCurrentSessionId: (id: string) => void
  
  // Analysis History - from app.py analysis history sidebar
  analysisReports: AnalysisReport[]
  setAnalysisReports: (reports: AnalysisReport[]) => void
  currentAnalysisId: string | null
  setCurrentAnalysisId: (id: string | null) => void
  
  // UI State
  sidebarCollapsed: boolean
  toggleSidebar: () => void
  showSettings: boolean
  setShowSettings: (show: boolean) => void
  
  // Analysis results
  analysisResult: unknown | null
  setAnalysisResult: (result: unknown | null) => void
  chartsCache: unknown[] | null
  setChartsCache: (charts: unknown[] | null) => void
  
  // Reset
  logout: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // User & Auth
      user: null,
      setUser: (user) => set({ user }),
      authToken: null,
      setAuthToken: (token) => set({ authToken: token }),
      
      // Mode
      mode: 'Analysis',
      setMode: (mode) => set({ mode }),
      
      // Domain
      domain: 'general',
      setDomain: (domain) => set({ domain }),
      
      // AI Engine
      useAgentMode: false,
      setUseAgentMode: (enabled) => set({ useAgentMode: enabled }),
      
      // Dataset
      currentDataset: null,
      setCurrentDataset: (dataset) => set({ currentDataset: dataset }),
      datasets: [],
      addDataset: (dataset) => {
        const { datasets } = get()
        const exists = datasets.find(d => d.hash === dataset.hash)
        if (!exists) {
          set({ datasets: [...datasets, dataset] })
        }
      },
      
      // Chat History
      chatSessions: [],
      addChatSession: (session) => {
        const { chatSessions } = get()
        set({ chatSessions: [...chatSessions, session] })
      },
      currentSessionId: crypto.randomUUID(),
      setCurrentSessionId: (id) => set({ currentSessionId: id }),
      
      // Analysis History
      analysisReports: [],
      setAnalysisReports: (reports) => set({ analysisReports: reports }),
      currentAnalysisId: null,
      setCurrentAnalysisId: (id) => set({ currentAnalysisId: id }),
      
      // UI State
      sidebarCollapsed: false,
      toggleSidebar: () => set(state => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      showSettings: false,
      setShowSettings: (show) => set({ showSettings: show }),
      
      // Analysis results
      analysisResult: null,
      setAnalysisResult: (result) => set({ analysisResult: result }),
      chartsCache: null,
      setChartsCache: (charts) => set({ chartsCache: charts }),
      
      // Reset
      logout: () => set({ 
        user: null, 
        authToken: null,
        currentDataset: null, 
        datasets: [],
        chatSessions: [],
        analysisReports: [],
        analysisResult: null,
        chartsCache: null,
      }),
    }),
    {
      name: 'vishleshak-app-storage',
      partialize: (state) => ({ 
        user: state.user, 
        authToken: state.authToken,
        domain: state.domain, 
        mode: state.mode,
        useAgentMode: state.useAgentMode,
      }),
    }
  )
)
