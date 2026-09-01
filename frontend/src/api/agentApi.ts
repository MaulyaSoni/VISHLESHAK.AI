/**
 * FastAPI Agent API Client
 * Connects React frontend to Week 3 FastAPI backend
 */

const FASTAPI_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Types
export interface AgentRunRequest {
  instruction: string
  mode: 'full' | 'eda' | 'ml'
  dataset_path?: string
}

export interface AgentRunResponse {
  job_id: string
  status: string
  message: string
}

export interface JobStatus {
  job_id: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  instruction: string
  mode: string
  steps: any[]
  report?: any
  error?: string
  created_at: number
  completed_at?: number
}

export interface UploadResponse {
  filename: string
  path: string
  size: number
}

/**
 * Start a new agent analysis job
 */
export async function runAgent(request: AgentRunRequest): Promise<AgentRunResponse> {
  const response = await fetch(`${FASTAPI_BASE_URL}/api/agent/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to start agent')
  }

  return response.json()
}

/**
 * Get job status
 */
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await fetch(`${FASTAPI_BASE_URL}/api/agent/status/${jobId}`)

  if (!response.ok) {
    throw new Error('Job not found')
  }

  return response.json()
}

/**
 * List all jobs
 */
export async function listJobs(): Promise<JobStatus[]> {
  const response = await fetch(`${FASTAPI_BASE_URL}/api/agent/jobs`)
  return response.json()
}

/**
 * Get final analysis report
 */
export async function getReport(jobId: string): Promise<any> {
  const response = await fetch(`${FASTAPI_BASE_URL}/api/agent/report/${jobId}`)

  if (!response.ok) {
    throw new Error('Report not available')
  }

  return response.json()
}

/**
 * Cancel a running job
 */
export async function cancelJob(jobId: string): Promise<{ status: string; job_id: string }> {
  const response = await fetch(`${FASTAPI_BASE_URL}/api/agent/cancel/${jobId}`, {
    method: 'POST'
  })

  if (!response.ok) {
    throw new Error('Failed to cancel job')
  }

  return response.json()
}

/**
 * Upload a dataset file
 */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${FASTAPI_BASE_URL}/api/files/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) {
    throw new Error('Upload failed')
  }

  return response.json()
}

/**
 * Connect to WebSocket for real-time updates
 */
export function connectWebSocket(jobId: string): WebSocket {
  const wsUrl = `ws://localhost:8000/ws/agent/${jobId}`
  return new WebSocket(wsUrl)
}

/**
 * Train a new ML model
 */
export async function trainModel(data: {
  instruction: string
  model_type: string
  target_column?: string
  features?: string[]
}): Promise<any> {
  const response = await fetch(`${FASTAPI_BASE_URL}/api/models/train`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
  })

  if (!response.ok) {
    throw new Error('Training failed')
  }

  return response.json()
}

/**
 * List all trained models
 */
export async function listModels(): Promise<any[]> {
  const response = await fetch(`${FASTAPI_BASE_URL}/api/models`)
  return response.json()
}

/**
 * Health check
 */
export async function healthCheck(): Promise<any> {
  const response = await fetch(`${FASTAPI_BASE_URL}/health`)
  return response.json()
}
