import { useEffect, useState } from 'react'
import { useAppStore, type AppMode } from '../../store/useAppStore'
import { 
  BarChart3, 
  MessageSquare, 
  Bot,
  Settings, 
  LogOut,
  History,
  Plus,
  ChevronRight,
  Microscope,
  Trash2,
  FolderOpen
} from 'lucide-react'
import { API_BASE_URL } from '@/api/client'

interface Conversation {
  id: number
  title: string
  dataset_name?: string
  created_at: string
  updated_at: string
}

interface AnalysisReport {
  id: number
  title: string
  instruction: string
  mode: string
  status: string
  created_at: string
}

const MODES: { key: AppMode; label: string; icon: typeof BarChart3 }[] = [
  { key: 'Analysis', label: 'Comprehensive Analysis', icon: BarChart3 },
  { key: 'Q&A', label: 'RAG Chatbot', icon: MessageSquare },
  { key: 'DataAgent', label: 'Data Agent', icon: Bot },
]

export function Sidebar() {
  const { 
    user, 
    mode,
    setMode,
    domain, 
    setDomain,
    useAgentMode,
    setUseAgentMode,
    chatSessions,
    currentSessionId,
    setCurrentSessionId,
    analysisReports,
    setAnalysisReports,
    setShowSettings,
    logout
  } = useAppStore()

  const [conversations, setConversations] = useState<Conversation[]>([])
  const [analyses, setAnalyses] = useState<AnalysisReport[]>([])
  const [loading, setLoading] = useState(false)

  // Fetch history from database
  useEffect(() => {
    if (!user) return
    
    const fetchHistory = async () => {
      setLoading(true)
      try {
        // Fetch conversations
        const convResponse = await fetch(`${API_BASE_URL}/api/history/conversations`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('vishleshak_token')}` }
        })
        if (convResponse.ok) {
          const convData = await convResponse.json()
          setConversations(convData.conversations || [])
        }
        
        // Fetch analyses
        const analysisResponse = await fetch(`${API_BASE_URL}/api/history/analyses`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('vishleshak_token')}` }
        })
        if (analysisResponse.ok) {
          const analysisData = await analysisResponse.json()
          setAnalyses(analysisData.analyses || [])
          setAnalysisReports(analysisData.analyses || [])
        }
      } catch (e) {
        console.error('Failed to fetch history:', e)
      }
      setLoading(false)
    }
    
    fetchHistory()
  }, [user, mode])

  const handleNewChat = async () => {
    // Create conversation in database and use its id as the session id
    try {
      const resp = await fetch(`${API_BASE_URL}/api/history/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('vishleshak_token')}`
        },
        body: JSON.stringify({ title: 'New Chat' })
      })
      if (resp.ok) {
        const created = await resp.json()
        setCurrentSessionId(String(created.id))
      } else {
        // Fallback to local-only session id if backend is unavailable
        setCurrentSessionId(crypto.randomUUID())
      }
    } catch (e) {
      console.error('Failed to create conversation:', e)
      setCurrentSessionId(crypto.randomUUID())
    }
  }
  
  const handleDeleteConversation = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await fetch(`${API_BASE_URL}/api/history/conversations/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('vishleshak_token')}` }
      })
      setConversations(conversations.filter(c => c.id !== id))
    } catch (e) {
      console.error('Failed to delete conversation:', e)
    }
  }
  
  const handleLoadAnalysis = async (id: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/history/analyses/${id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('vishleshak_token')}` }
      })
      if (response.ok) {
        const data = await response.json()
        // Store in app state and switch to DataAgent mode
        setMode('DataAgent')
        // The DataAgentMode component will need to check for this
        localStorage.setItem('vishleshak_loaded_analysis', JSON.stringify(data))
      }
    } catch (e) {
      console.error('Failed to load analysis:', e)
    }
  }

  return (
    <aside className="w-[280px] bg-bg-surface border-r border-border-subtle flex flex-col h-full">
      {/* Brand Header */}
      <div className="p-4 border-b border-border-subtle">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-blue to-accent-cyan flex items-center justify-center text-white text-xl">
            <Microscope className="w-6 h-6" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="font-bold text-text-primary text-lg">Vishleshak AI</h1>
            {user && (
              <p className="text-xs text-text-muted truncate">👤 {user.username}</p>
            )}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {/* User Actions */}
        {user && (
          <div className="p-3 grid grid-cols-2 gap-2">
            <button 
              onClick={() => setShowSettings(true)}
              className="btn-secondary text-sm py-2 flex items-center justify-center gap-1"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
            <button 
              onClick={logout}
              className="btn-secondary text-sm py-2 flex items-center justify-center gap-1"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        )}

        {/* Mode Selector - like app.py radio buttons */}
        <div className="sidebar-section">Mode</div>
        <div className="px-3 space-y-1">
          {MODES.map(({ key, label, icon: Icon }) => (
            <label 
              key={key}
              className={`mode-radio ${mode === key ? 'active' : ''}`}
              onClick={() => setMode(key)}
            >
              <input 
                type="radio" 
                name="mode" 
                checked={mode === key}
                onChange={() => setMode(key)}
                className="w-4 h-4 accent-accent-blue"
              />
              <Icon className={`w-5 h-5 ${mode === key ? 'text-accent-blue' : 'text-text-muted'}`} />
              <span className={`text-sm ${mode === key ? 'text-text-primary font-medium' : 'text-text-muted'}`}>
                {label}
              </span>
            </label>
          ))}
        </div>

        {/* AI Engine Toggle - Analysis mode only */}
        {mode === 'Analysis' && (
          <>
            <div className="sidebar-section">AI Engine</div>
            <div className="px-4 py-2">
              <label className="flex items-center gap-3 cursor-pointer">
                <input 
                  type="checkbox"
                  checked={useAgentMode}
                  onChange={(e) => setUseAgentMode(e.target.checked)}
                  className="w-4 h-4 rounded accent-accent-blue"
                />
                <span className="text-sm text-text-primary">Use Multi-Agent Supervisor (v2)</span>
              </label>
              
              {useAgentMode && (
                <div className="mt-3">
                  <select
                    value={domain}
                    onChange={(e) => setDomain(e.target.value as any)}
                    className="w-full input text-sm"
                  >
                    <option value="general">🎯 General</option>
                    <option value="finance">🎯 Finance</option>
                    <option value="insurance">🎯 Insurance</option>
                    <option value="ecommerce">🎯 E-commerce</option>
                  </select>
                </div>
              )}
            </div>
          </>
        )}

        {/* Chat History - Q&A mode only */}
        {mode === 'Q&A' && (
          <>
            <div className="sidebar-section flex items-center justify-between">
              <span>Chat History</span>
              <button 
                onClick={handleNewChat}
                className="text-accent-blue hover:text-accent-cyan"
              >
                <Plus className="w-4 h-4" />
              </button>
            </div>
            <div className="px-2 space-y-1">
              {loading ? (
                <div className="px-3 py-4 text-sm text-text-muted text-center">
                  Loading...
                </div>
              ) : conversations.length === 0 ? (
                <div className="px-3 py-4 text-sm text-text-muted text-center">
                  No chat history yet.
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.id}
                    onClick={() => setCurrentSessionId(String(conv.id))}
                    className={`history-item flex items-center gap-2 group ${
                      String(conv.id) === currentSessionId ? 'active' : ''
                    }`}
                  >
                    <span>{String(conv.id) === currentSessionId ? '💬' : '🕐'}</span>
                    <span className="truncate flex-1">{conv.title}</span>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="opacity-0 group-hover:opacity-100 text-text-muted hover:text-red-400 transition-opacity"
                    >
                      <Trash2 className="w-3 h-3" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </>
        )}

        {/* Analysis History */}
        {user && (
          <>
            <div className="sidebar-section">📊 Analysis History</div>
            <div className="px-2 space-y-1">
              {loading ? (
                <div className="px-3 py-4 text-sm text-text-muted text-center">
                  Loading...
                </div>
              ) : analyses.length === 0 ? (
                <div className="px-3 py-4 text-sm text-text-muted text-center">
                  No analysis history yet.
                </div>
              ) : (
                analyses.slice(0, 10).map((report) => (
                  <div
                    key={report.id}
                    onClick={() => handleLoadAnalysis(report.id)}
                    className="px-3 py-2 rounded-lg cursor-pointer hover:bg-bg-elevated transition-colors group"
                    style={{
                      borderLeft: '3px solid #4fc3f7',
                      background: 'rgba(79,195,247,0.1)',
                      margin: '4px 0'
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <FolderOpen className="w-3 h-3 text-accent-blue opacity-0 group-hover:opacity-100 transition-opacity" />
                      <div className="text-sm text-text-primary truncate flex-1">
                        {report.title.slice(0, 30)}...
                      </div>
                    </div>
                    <div className="text-xs text-text-muted mt-1">
                      {new Date(report.created_at).toLocaleDateString()} • {report.mode}
                    </div>
                  </div>
                ))
              )}
              {analyses.length === 10 && (
                <div className="px-3 py-2 text-xs text-text-muted text-center">
                  Showing last 10 analyses...
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-border-subtle">
        <div className="text-xs text-text-muted text-center">
          Vishleshak AI v1.0.0
        </div>
      </div>
    </aside>
  )
}
