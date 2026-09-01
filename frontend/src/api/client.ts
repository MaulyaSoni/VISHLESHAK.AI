export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'
export const API_BASE_URL = API_BASE // For compatibility

export function getToken(): string | null {
  return localStorage.getItem('access_token') ||
         localStorage.getItem('token') ||
         localStorage.getItem('vishleshak_token') ||
         sessionStorage.getItem('access_token')
}

export function authHeaders(isFormData: boolean = false): Record<string, string> {
  const token = getToken()
  const headers: Record<string, string> = {}
  
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  return headers
}

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  // Ensure path starts with /
  const cleanPath = path.startsWith('http') ? path : `${API_BASE}${path.startsWith('/') ? '' : '/'}${path}`
  
  const isFormData = options.body instanceof FormData
  const baseHeaders = authHeaders(isFormData)
  
  const headers = {
    ...baseHeaders,
    ...(options.headers || {}),
  }

  // If Content-Type is specifically set to 'undefined', delete it
  if (headers['Content-Type'] === 'undefined') {
    delete headers['Content-Type']
  }

  const response = await fetch(cleanPath, {
    ...options,
    headers
  })

  if (response.status === 401 && !cleanPath.includes('/auth/login')) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('token')
    localStorage.removeItem('vishleshak_token')
    // Only redirect if not already on login page
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }

  return response
}

// Simple axios-like wrapper for existing code
export const apiClient = {
  get: async (path: string, options: any = {}) => {
    const res = await apiFetch(path, { ...options, method: 'GET' })
    if (!res.ok) {
      const error = await res.json().catch(() => ({}))
      throw { response: { data: error, status: res.status } }
    }
    return { data: await res.json() }
  },
  post: async (path: string, body?: any, options: any = {}) => {
    const res = await apiFetch(path, { ...options, method: 'POST', body })
    if (!res.ok) {
      const error = await res.json().catch(() => ({}))
      throw { response: { data: error, status: res.status } }
    }
    return { data: await res.json() }
  },
  delete: async (path: string, options: any = {}) => {
    const res = await apiFetch(path, { ...options, method: 'DELETE' })
    if (!res.ok) {
      const error = await res.json().catch(() => ({}))
      throw { response: { data: error, status: res.status } }
    }
    return { data: await res.json() }
  }
}
