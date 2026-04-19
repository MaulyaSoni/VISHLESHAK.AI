import { useAppStore } from '../../store/useAppStore'
import { useAgentStore } from '../../store/useAgentStore'
import { User, Activity, Bell } from 'lucide-react'

export function TopBar() {
  const { user, currentDataset } = useAppStore()
  const { status } = useAgentStore()

  const statusConfig = {
    idle: { color: 'bg-text-muted', text: 'Idle' },
    running: { color: 'bg-accent-blue animate-pulse', text: 'Running' },
    done: { color: 'bg-accent-green', text: 'Done' },
    error: { color: 'bg-accent-red', text: 'Error' },
  }

  return (
    <header className="h-12 bg-bg-surface border-b border-border-subtle flex items-center justify-between px-4">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-text-muted">Workspace</span>
        {currentDataset && (
          <>
            <span className="text-text-muted">/</span>
            <span className="text-text-primary">{currentDataset.filename}</span>
          </>
        )}
      </div>

      {/* Center - Agent Status */}
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${statusConfig[status].color}`} />
        <span className="text-sm text-text-muted">{statusConfig[status].text}</span>
      </div>

      {/* Right - User & Notifications */}
      <div className="flex items-center gap-4">
        <button className="relative p-2 hover:bg-bg-elevated rounded-lg transition-colors">
          <Bell className="w-5 h-5 text-text-muted" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-accent-red rounded-full" />
        </button>
        
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-full bg-accent-blue/20 flex items-center justify-center">
            <User className="w-4 h-4 text-accent-blue" />
          </div>
          <span className="text-sm text-text-primary hidden sm:block">
            {user?.username}
          </span>
        </div>
      </div>
    </header>
  )
}
