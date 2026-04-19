import { useMutation } from '@tanstack/react-query'
import { apiClient } from './client'
import type { Dataset } from '@/store/useAppStore'

interface UploadResponse {
  dataset_hash: string
  filename: string
  rows: number
  cols: number
  meta: Record<string, unknown>
}

interface ScanResponse {
  files: Array<{
    name: string
    path: string
    size_mb: number
    modified: string
  }>
}

export const filesApi = {
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const { data } = await apiClient.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return data
  },
  
  scan: async (folderPath: string): Promise<ScanResponse> => {
    const { data } = await apiClient.post('/files/scan', { folder_path: folderPath })
    return data
  },
  
  loadPath: async (filePath: string): Promise<UploadResponse> => {
    const { data } = await apiClient.post('/files/load-path', { file_path: filePath })
    return data
  },
}

// React Query hooks
export const useUploadFile = () => {
  return useMutation({
    mutationFn: filesApi.upload,
  })
}

export const useScanFolder = () => {
  return useMutation({
    mutationFn: filesApi.scan,
  })
}

export const useLoadPath = () => {
  return useMutation({
    mutationFn: filesApi.loadPath,
  })
}
