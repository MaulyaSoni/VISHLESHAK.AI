import { useMutation } from '@tanstack/react-query'
import { apiClient } from './client'
import { API_BASE_URL } from './client'
import { useAgentStore } from '@/store/useAgentStore'

interface RunAnalysisRequest {
  query: string
  dataset_hash: string
  domain: string
  mode: 'analysis_only' | 'analysis_ml' | 'analysis_ml_notebook'
}

interface RunAnalysisResponse {
  session_id: string
}

export const analysisApi = {
  run: async (request: RunAnalysisRequest): Promise<RunAnalysisResponse> => {
    const { data } = await apiClient.post('/analysis/run', request)
    return data
  },
}

// SSE streaming hook
export const useStreamAnalysis = () => {
  const { 
    setStatus, 
    setProgress, 
    addTraceStep, 
    addChart, 
    setInsights,
    addFlag,
    setFinalResult,
    setError,
  } = useAgentStore()

  const startStreaming = (sessionId: string) => {
    const eventSource = new EventSource(`${API_BASE_URL}/api/analysis/stream?session_id=${sessionId}`)
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        
        switch (data.type) {
          case 'trace':
            addTraceStep({
              id: `${Date.now()}-${Math.random()}`,
              agent: data.agent,
              action: data.action,
              output: data.output,
              timestamp: Date.now(),
            })
            break
            
          case 'progress':
            setProgress(data.progress || 0)
            break
            
          case 'chart':
            addChart({
              id: `${Date.now()}-${Math.random()}`,
              path: data.path,
              caption: data.caption,
              type: data.chart_type || 'unknown',
            })
            break
            
          case 'insight':
            setInsights(data.text)
            break
            
          case 'flag':
            addFlag({
              severity: data.severity,
              icon: data.icon,
              message: data.message,
            })
            break
            
          case 'done':
            setStatus('done')
            setFinalResult(data.final_response, data.pdf_path)
            eventSource.close()
            break
            
          case 'error':
            setStatus('error')
            setError(data.message)
            eventSource.close()
            break
        }
      } catch (err) {
        console.error('Failed to parse SSE event:', err)
      }
    }
    
    eventSource.onerror = () => {
      setStatus('error')
      setError('Connection lost')
      eventSource.close()
    }
    
    return () => eventSource.close()
  }

  return { startStreaming }
}

export const useRunAnalysis = () => {
  const { setStatus } = useAgentStore()
  const { startStreaming } = useStreamAnalysis()
  
  return useMutation({
    mutationFn: analysisApi.run,
    onSuccess: (data) => {
      setStatus('running')
      startStreaming(data.session_id)
    },
  })
}
