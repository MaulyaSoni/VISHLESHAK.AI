import { useState, useEffect, useCallback, useRef } from 'react'
import { runAgent, getJobStatus, cancelJob, connectWebSocket, JobStatus } from '../api/agentApi'
import { toast } from '../components/shared'
import { StatusType } from '../components/shared/StatusPill'

interface UseAgentJobOptions {
  onSuccess?: (report: any) => void
  onError?: (error: string) => void
  onStatusChange?: (status: StatusType) => void
}

export function useAgentJob(options?: UseAgentJobOptions) {
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<StatusType>('idle')
  const [jobData, setJobData] = useState<JobStatus | null>(null)
  const [isRunning, setIsRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)

  // Map job status to UI status
  const mapStatus = (jobStatus: string): StatusType => {
    switch (jobStatus) {
      case 'pending': return 'idle'
      case 'running': return 'running'
      case 'completed': return 'done'
      case 'failed': return 'error'
      case 'cancelled': return 'cancelled'
      default: return 'idle'
    }
  }

  // Update job status
  const updateJobData = useCallback((data: JobStatus) => {
    setJobData(data)
    const newStatus = mapStatus(data.status)
    setStatus(newStatus)
    setIsRunning(data.status === 'running')
    
    options?.onStatusChange?.(newStatus)
  }, [options])

  // Start a new job
  const startJob = useCallback(async (instruction: string, mode: 'full' | 'eda' | 'ml' = 'full') => {
    try {
      setError(null)
      setStatus('running')
      setIsRunning(true)
      
      const response = await runAgent({ instruction, mode })
      setJobId(response.job_id)
      
      toast.info('Analysis started', 3000)
      
      // Connect WebSocket
      const ws = connectWebSocket(response.job_id)
      wsRef.current = ws
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          updateJobData(data as JobStatus)
        } catch (e) {
          console.error('WebSocket message parse error:', e)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        toast.error('Connection lost, polling for updates...')
        // Fallback to polling
        startPolling(response.job_id)
      }
      
      ws.onclose = () => {
        wsRef.current = null
      }
      
      return response.job_id
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to start job'
      setError(errorMsg)
      setStatus('error')
      setIsRunning(false)
      toast.error(errorMsg)
      options?.onError?.(errorMsg)
      throw err
    }
  }, [options, updateJobData])

  // Poll for updates (fallback)
  const startPolling = useCallback(async (id: string) => {
    const poll = async () => {
      try {
        const data = await getJobStatus(id)
        updateJobData(data)
        
        if (data.status === 'completed') {
          setIsRunning(false)
          toast.success('Analysis complete!')
          options?.onSuccess?.(data.report)
        } else if (data.status === 'failed') {
          setIsRunning(false)
          setError(data.error || 'Job failed')
          toast.error('Analysis failed')
          options?.onError?.(data.error || 'Job failed')
        } else if (data.status === 'running') {
          // Continue polling
          setTimeout(poll, 2000)
        }
      } catch (err: any) {
        console.error('Polling error:', err)
      }
    }
    
    poll()
  }, [options, updateJobData])

  // Cancel job
  const cancelJobHandler = useCallback(async () => {
    if (!jobId) return
    
    try {
      await cancelJob(jobId)
      setStatus('cancelled')
      setIsRunning(false)
      toast.warning('Job cancelled')
      
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    } catch (err: any) {
      toast.error('Failed to cancel job')
    }
  }, [jobId])

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [])

  return {
    jobId,
    status,
    jobData,
    isRunning,
    error,
    startJob,
    cancelJob: cancelJobHandler,
    reset: () => {
      setJobId(null)
      setStatus('idle')
      setJobData(null)
      setIsRunning(false)
      setError(null)
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }
}
