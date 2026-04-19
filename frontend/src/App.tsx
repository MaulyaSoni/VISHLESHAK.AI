import { useState, useEffect } from 'react'
import { useAppStore } from './store/useAppStore'
import { Sidebar } from './components/layout/Sidebar'
import { AnalysisMode } from './components/modes/AnalysisMode'
import { ChatbotMode } from './components/modes/ChatbotMode'
import { DataAgentMode } from './components/modes/DataAgentMode'
import { Loader2, Mail, Lock, Database } from 'lucide-react'
import { API_BASE_URL } from './api/client'

// Login Component
function LoginPage({ onLogin }: { onLogin: (email: string, password: string) => Promise<void> }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    
    try {
      await onLogin(email, password)
    } catch (err: any) {
      setError(err.message || 'Login failed')
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
          <h2 className="text-xl font-semibold mb-6">Sign In</h2>
          
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-accent-red text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
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
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>
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
      const token = localStorage.getItem('vishleshak_token')
      if (token) {
        try {
          // Verify token with backend
          const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          })
          
          if (response.ok) {
            const userData = await response.json()
            setAuthToken(token)
            setUser(userData)
          } else {
            // Token invalid, remove it
            localStorage.removeItem('vishleshak_token')
          }
        } catch (e) {
          // Backend not available, use dev mode
          console.warn('Backend not available, running in dev mode')
        }
      }
      setIsLoading(false)
    }
    
    checkAuth()
  }, [setUser, setAuthToken])

  const handleLogin = async (email: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.error || 'Login failed')
    }
    
    const data = await response.json()
    localStorage.setItem('vishleshak_token', data.token)
    setAuthToken(data.token)
    setUser(data.user)
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
    return <LoginPage onLogin={handleLogin} />
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
