import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search, Command, FileText, Database, MessageSquare, Settings, X } from 'lucide-react'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

interface Command {
  id: string
  label: string
  description: string
  icon: any
  category: string
  action: () => void
}

export function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)

  const commands: Command[] = [
    {
      id: 'data-agent',
      label: 'Open Data Agent',
      description: 'Start automated analysis',
      icon: Database,
      category: 'Navigation',
      action: () => navigate('/workspace?mode=DataAgent')
    },
    {
      id: 'chat',
      label: 'Open Chat',
      description: 'Chat with AI assistant',
      icon: MessageSquare,
      category: 'Navigation',
      action: () => navigate('/chat')
    },
    {
      id: 'analysis',
      label: 'Open Analysis',
      description: 'Manual data exploration',
      icon: FileText,
      category: 'Navigation',
      action: () => navigate('/workspace?mode=Analysis')
    },
    {
      id: 'kaggle',
      label: 'Browse Kaggle',
      description: 'Search datasets',
      icon: Database,
      category: 'Navigation',
      action: () => navigate('/kaggle')
    },
    {
      id: 'memory',
      label: 'View Memory',
      description: 'AI context and memories',
      icon: FileText,
      category: 'Navigation',
      action: () => navigate('/memory')
    },
    {
      id: 'benchmarks',
      label: 'View Benchmarks',
      description: 'Performance metrics',
      icon: FileText,
      category: 'Navigation',
      action: () => navigate('/benchmarks')
    },
    {
      id: 'settings',
      label: 'Settings',
      description: 'App configuration',
      icon: Settings,
      category: 'Preferences',
      action: () => navigate('/settings')
    }
  ]

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(search.toLowerCase()) ||
      cmd.description.toLowerCase().includes(search.toLowerCase())
  )

  useEffect(() => {
    if (isOpen) {
      setSearch('')
      setSelectedIndex(0)
    }
  }, [isOpen])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.min(prev + 1, filteredCommands.length - 1))
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex((prev) => Math.max(prev - 1, 0))
      } else if (e.key === 'Enter' && filteredCommands[selectedIndex]) {
        e.preventDefault()
        filteredCommands[selectedIndex].action()
        onClose()
      } else if (e.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredCommands, selectedIndex, onClose])

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[20vh] px-4">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      {/* Palette */}
      <div className="relative w-full max-w-2xl card border-border-subtle shadow-2xl animate-in fade-in zoom-in duration-200">
        {/* Search Input */}
        <div className="flex items-center gap-3 p-4 border-b border-border-subtle">
          <Search className="w-5 h-5 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Type a command or search..."
            className="flex-1 bg-transparent text-text-primary placeholder:text-text-muted focus:outline-none"
            autoFocus
          />
          <kbd className="px-2 py-1 rounded bg-bg-elevated text-xs text-text-muted border border-border-subtle">
            ESC
          </kbd>
        </div>

        {/* Commands List */}
        <div className="max-h-[400px] overflow-y-auto p-2">
          {filteredCommands.length === 0 ? (
            <div className="p-8 text-center text-text-muted">
              <Command className="w-8 h-8 mx-auto mb-2" />
              <p>No commands found</p>
            </div>
          ) : (
            <>
              {filteredCommands.map((cmd, index) => {
                const Icon = cmd.icon
                return (
                  <button
                    key={cmd.id}
                    onClick={() => {
                      cmd.action()
                      onClose()
                    }}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors ${
                      index === selectedIndex
                        ? 'bg-accent-blue/10 text-accent-blue'
                        : 'hover:bg-bg-elevated text-text-primary'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <div className="flex-1 text-left">
                      <p className="text-sm font-medium">{cmd.label}</p>
                      <p className="text-xs text-text-muted">{cmd.description}</p>
                    </div>
                    <span className="text-xs text-text-muted px-2 py-1 rounded bg-bg-elevated border border-border-subtle">
                      {cmd.category}
                    </span>
                  </button>
                )
              })}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-border-subtle flex items-center gap-4 text-xs text-text-muted">
          <div className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle">↑</kbd>
            <kbd className="px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle">↓</kbd>
            <span>to navigate</span>
          </div>
          <div className="flex items-center gap-1">
            <kbd className="px-1.5 py-0.5 rounded bg-bg-elevated border border-border-subtle">↵</kbd>
            <span>to select</span>
          </div>
        </div>
      </div>
    </div>
  )
}
