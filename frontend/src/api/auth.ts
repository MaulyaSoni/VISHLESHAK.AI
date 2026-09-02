import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from './client'
import type { User } from '@/store/useAppStore'
import { normalizeUserPayload } from '@/utils/auth'

interface LoginCredentials {
  email: string
  password: string
}

interface LoginResponse {
  token: string
  user: User
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const { data } = await apiClient.post('/auth/login', credentials)
    const user = normalizeUserPayload(data)

    if (!data?.token || !user) {
      throw new Error('Invalid login response from server')
    }

    return {
      token: data.token,
      user,
    }
  },
  
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },
  
  me: async (): Promise<User> => {
    const { data } = await apiClient.get('/auth/me')
    const user = normalizeUserPayload(data)

    if (!user) {
      throw new Error('Invalid user response from server')
    }

    return user
  },
}

// React Query hooks
export const useLogin = () => {
  return useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      localStorage.setItem('vishleshak_token', data.token)
    },
  })
}

export const useLogout = () => {
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      localStorage.removeItem('vishleshak_token')
    },
  })
}

export const useMe = () => {
  return useQuery({
    queryKey: ['me'],
    queryFn: authApi.me,
    retry: false,
  })
}
