import { AppShell } from '../components/layout/AppShell'
import { useAppStore } from '../store/useAppStore'
import { useLogout } from '../api/auth'
import { useNavigate } from 'react-router-dom'
import { 
  User, 
  Database, 
  Trash2, 
  LogOut,
  Shield,
  Bell
} from 'lucide-react'

export default function SettingsPage() {
  const navigate = useNavigate()
  const { user, domain, setDomain, logout } = useAppStore()
  const logoutMutation = useLogout()

  const handleLogout = async () => {
    await logoutMutation.mutateAsync()
    logout()
    navigate('/login')
  }

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto p-8">
        <h1 className="text-2xl font-semibold mb-8">Settings</h1>

        <div className="space-y-6">
          {/* Profile Section */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <User className="w-5 h-5 text-accent-blue" />
              <h2 className="text-lg font-medium">Profile</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm text-text-muted">Email</label>
                <p className="text-text-primary">{user?.email}</p>
              </div>
              <div>
                <label className="text-sm text-text-muted">Username</label>
                <p className="text-text-primary">{user?.username}</p>
              </div>
            </div>
          </div>

          {/* Domain Section */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-5 h-5 text-accent-blue" />
              <h2 className="text-lg font-medium">Domain</h2>
            </div>
            
            <div className="flex gap-3">
              {(['finance', 'insurance', 'general'] as const).map((d) => (
                <button
                  key={d}
                  onClick={() => setDomain(d)}
                  className={`px-4 py-2 rounded-lg capitalize transition-colors ${
                    domain === d
                      ? 'bg-accent-blue text-white'
                      : 'bg-bg-elevated text-text-muted hover:text-text-primary'
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {/* Memory Section */}
          <div className="card p-6">
            <div className="flex items-center gap-3 mb-4">
              <Database className="w-5 h-5 text-accent-blue" />
              <h2 className="text-lg font-medium">Memory</h2>
            </div>
            
            <div className="flex items-center justify-between py-3 border-b border-border-subtle">
              <div>
                <p className="text-text-primary">Clear Conversation History</p>
                <p className="text-sm text-text-muted">Remove all chat history</p>
              </div>
              <button className="btn-secondary flex items-center gap-2">
                <Trash2 className="w-4 h-4" />
                Clear
              </button>
            </div>
            
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="text-text-primary">Clear All Memory</p>
                <p className="text-sm text-text-muted">Remove all stored data</p>
              </div>
              <button className="btn-secondary flex items-center gap-2 text-accent-red hover:text-accent-red">
                <Trash2 className="w-4 h-4" />
                Clear All
              </button>
            </div>
          </div>

          {/* Logout */}
          <div className="card p-6">
            <button
              onClick={handleLogout}
              disabled={logoutMutation.isPending}
              className="flex items-center gap-2 text-accent-red hover:text-accent-red/80 transition-colors"
            >
              <LogOut className="w-5 h-5" />
              {logoutMutation.isPending ? 'Signing out...' : 'Sign Out'}
            </button>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
