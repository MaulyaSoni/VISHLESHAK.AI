import { create } from 'zustand'

export type AgentStatus = 'idle' | 'running' | 'done' | 'error'

export interface TraceStep {
  id: string
  agent: string
  action: string
  output: string
  timestamp: number
}

export interface Chart {
  id: string
  path: string
  caption: string
  type: string
}

export interface AgentState {
  // Status
  status: AgentStatus
  progress: number
  setStatus: (status: AgentStatus) => void
  setProgress: (progress: number) => void
  
  // Trace
  traceSteps: TraceStep[]
  addTraceStep: (step: TraceStep) => void
  clearTrace: () => void
  
  // Charts
  charts: Chart[]
  addChart: (chart: Chart) => void
  clearCharts: () => void
  
  // Insights
  insights: string
  setInsights: (insights: string) => void
  
  // Flags
  flags: Array<{ severity: string; icon: string; message: string }>
  addFlag: (flag: { severity: string; icon: string; message: string }) => void
  clearFlags: () => void
  
  // Final result
  finalResponse: string | null
  pdfPath: string | null
  setFinalResult: (response: string, pdfPath?: string) => void
  
  // Error
  error: string | null
  setError: (error: string | null) => void
  
  // Reset
  reset: () => void
}

export const useAgentStore = create<AgentState>((set) => ({
  // Status
  status: 'idle',
  progress: 0,
  setStatus: (status) => set({ status }),
  setProgress: (progress) => set({ progress }),
  
  // Trace
  traceSteps: [],
  addTraceStep: (step) => set((state) => ({ 
    traceSteps: [...state.traceSteps, step] 
  })),
  clearTrace: () => set({ traceSteps: [] }),
  
  // Charts
  charts: [],
  addChart: (chart) => set((state) => ({ 
    charts: [...state.charts, chart] 
  })),
  clearCharts: () => set({ charts: [] }),
  
  // Insights
  insights: '',
  setInsights: (insights) => set({ insights }),
  
  // Flags
  flags: [],
  addFlag: (flag) => set((state) => ({ 
    flags: [...state.flags, flag] 
  })),
  clearFlags: () => set({ flags: [] }),
  
  // Final result
  finalResponse: null,
  pdfPath: null,
  setFinalResult: (finalResponse, pdfPath) => set({ finalResponse, pdfPath }),
  
  // Error
  error: null,
  setError: (error) => set({ error }),
  
  // Reset
  reset: () => set({
    status: 'idle',
    progress: 0,
    traceSteps: [],
    charts: [],
    insights: '',
    flags: [],
    finalResponse: null,
    pdfPath: null,
    error: null,
  }),
}))
