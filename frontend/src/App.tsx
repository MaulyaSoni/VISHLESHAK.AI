import { useState, useEffect } from 'react'
import { useAppStore } from './store/useAppStore'
import { Sidebar } from './components/layout/Sidebar'
import { AnalysisMode } from './components/modes/AnalysisMode'
import { ChatbotMode } from './components/modes/ChatbotMode'
import { DataAgentMode } from './components/modes/DataAgentMode'
import { Loader2, Mail, Lock, Database } from 'lucide-react'
import { API_BASE_URL, apiFetch } from './api/client'
import { normalizeUserPayload } from './utils/auth'

// Login / Register Component
function LoginPage({ onAuth }: { onAuth: (type: 'login' | 'register', email: string, password: string, name?: string) => Promise<void> }) {
  const [isRegister, setIsRegister] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    
    try {
      if (isRegister) {
        await onAuth('register', email, password, name)
      } else {
        await onAuth('login', email, password)
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bg-base flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-accent-blue/10 mb-4">
            <Database className="w-8 h-8 text-accent-blue" />
          </div>
          <h1 className="text-2xl font-semibold text-text-primary mb-1">
            Vishleshak AI
          </h1>
          <p className="text-text-muted">The Analyser of Your Financial Data</p>
        </div>

        {/* Login Card */}
        <div className="card p-8">
          <h2 className="text-xl font-semibold mb-6">{isRegister ? 'Create Account' : 'Sign In'}</h2>
          
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-accent-red text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {isRegister && (
              <div>
                <label className="block text-sm font-medium text-text-muted mb-1">
                  Full Name
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="input w-full pl-3"
                    placeholder="Your Name"
                    required
                  />
                </div>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-text-muted mb-1">
                Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="input w-full pl-10"
                  placeholder="you@example.com"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-muted mb-1">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="input w-full pl-10"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {isRegister ? 'Creating Account...' : 'Signing in...'}
                </>
              ) : (
                isRegister ? 'Sign Up' : 'Sign In'
              )}
            </button>
          </form>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => { setIsRegister(!isRegister); setError(''); }}
              className="text-sm text-accent-blue hover:underline"
            >
              {isRegister ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
            </button>
          </div>
        </div>

        <p className="text-center text-text-muted text-sm mt-6">
          Finance & Insurance Intelligence Platform
        </p>
      </div>
    </div>
  )
}

function App() {
  const { user, mode, setUser, setAuthToken } = useAppStore()
  const [isLoading, setIsLoading] = useState(true)

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token') || 
                    localStorage.getItem('token') || 
                    localStorage.getItem('vishleshak_token') ||
                    sessionStorage.getItem('access_token')

      if (!token) {
        setAuthToken(null)
        setUser(null)
        setIsLoading(false)
        return
      }

      try {
        const response = await apiFetch('/api/auth/me', {
          method: 'GET'
        })

        if (response.status === 401 || response.status === 403) {
          // Token expired or invalid — clear it
          localStorage.removeItem('access_token')
          localStorage.removeItem('token')
          localStorage.removeItem('vishleshak_token')
          sessionStorage.removeItem('access_token')
          setAuthToken(null)
          setUser(null)
          setIsLoading(false)
          return
        }

        if (!response.ok) {
          setAuthToken(null)
          setUser(null)
          setIsLoading(false)
          return
        }

        const data = await response.json()
        const normalizedUser = normalizeUserPayload(data)
        
        if (!normalizedUser) {
          setAuthToken(null)
          setUser(null)
          setIsLoading(false)
          return
        }

        setAuthToken(token)
        setUser(normalizedUser)
      } catch (err) {
        console.error('Auth check failed:', err)
        setAuthToken(null)
        setUser(null)
      } finally {
        setIsLoading(false)
      }
    }
    
    checkAuth()
  }, [setUser, setAuthToken])

  const handleAuth = async (type: 'login' | 'register', email: string, password: string, name?: string) => {
    const endpoint = type === 'register' ? '/api/auth/register' : '/api/auth/login'
    
    // Ensure username is at least 3 characters for backend validation
    const generatedUsername = email.split('@')[0]
    const safeUsername = generatedUsername.length >= 3 ? generatedUsername : generatedUsername + Math.floor(Math.random() * 1000).toString().padStart(3, '0')

    // Build payload checking if it is register or not
    const basePayload = type === 'register' 
      ? { email, password, username: safeUsername, full_name: name || safeUsername }
      : { email, password }

    const response = await apiFetch(endpoint, {
      method: 'POST',
      body: JSON.stringify(basePayload)
    })
    
    if (!response.ok) {
      let message = `${type === 'register' ? 'Registration' : 'Login'} failed`
      try {
        const error = await response.json()
        if (error.detail && Array.isArray(error.detail)) {
          message = error.detail.map((d: any) => d.msg || 'Invalid input').join(', ')
        } else {
          message = error.error || error.detail || message
        }
      } catch {
        // Ignore parse failure
      }
      throw new Error(message)
    }
    
    const data = await response.json()
    
    if (type === 'register') {
      // After successful registration, automatically log in
      return handleAuth('login', email, password)
    }

    const normalizedUser = normalizeUserPayload(data)

    if (!data?.token || !normalizedUser) {
      throw new Error('Invalid authentication response from server')
    }

    localStorage.setItem('vishleshak_token', data.token)
    localStorage.setItem('access_token', data.token)
    localStorage.setItem('token', data.token)
    setAuthToken(data.token)
    setUser(normalizedUser)
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-base flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-blue" />
      </div>
    )
  }

  // Show login page if not authenticated
  if (!user) {
    return <LoginPage onAuth={handleAuth} />
  }

  return (
    <div className="min-h-screen bg-bg-base flex">
      <Sidebar />
      
      <main className="flex-1 min-w-0 overflow-hidden">
        {mode === 'Analysis' && <AnalysisMode />}
        {mode === 'Q&A' && <ChatbotMode />}
        {mode === 'DataAgent' && <DataAgentMode />}
      </main>
    </div>
  )
}

export default App
