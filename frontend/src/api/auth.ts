import { useMutation, useQuery } from '@tanstack/react-query'
import { apiClient } from './client'
import type { User } from '@/store/useAppStore'

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
    return data
  },
  
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout')
  },
  
  me: async (): Promise<User> => {
    const { data } = await apiClient.get('/auth/me')
    return data
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
