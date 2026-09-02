import { useState, useEffect } from 'react'
import { Brain, Calendar, Tag, Loader2 } from 'lucide-react'
import { apiFetch } from '../api/client'

interface Memory {
  id: string
  content: string
  importance: number
  created_at: Date
  tags: string[]
  context: string
}

export function MemoryViewer() {
  const [memories, setMemories] = useState<Memory[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'important' | 'recent'>('all')

  useEffect(() => {
    loadMemories()
  }, [])

  const loadMemories = async () => {
    try {
      const response = await apiFetch('/api/memory')

      if (!response.ok) throw new Error('Failed to load memory')

      const data = await response.json()
      setMemories(data.memories || [])
    } catch (error) {
      console.error('Load memories error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const filteredMemories = memories.filter((memory) => {
    if (filter === 'important') return memory.importance >= 0.7
    if (filter === 'recent') {
      const sevenDaysAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
      return new Date(memory.created_at) > sevenDaysAgo
    }
    return true
  })

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - new Date(date).getTime()
    const days = Math.floor(diff / (1000 * 60 * 60 * 24))
    
    if (days === 0) return 'Today'
    if (days === 1) return 'Yesterday'
    if (days < 7) return `${days} days ago`
    return new Date(date).toLocaleDateString()
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary mb-2 flex items-center gap-3">
          <Brain className="w-6 h-6 text-accent-cyan" />
          Memory & Context
        </h1>
        <p className="text-text-muted">
          AI memories and context from your previous interactions
        </p>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6">
        {(['all', 'important', 'recent'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              'px-4 py-2 rounded-lg text-sm font-medium transition-all',
              filter === f
                ? 'bg-accent-blue text-white'
                : 'bg-bg-elevated text-text-muted hover:text-text-primary'
            )}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-accent-blue" />
        </div>
      )}

      {/* Memories List */}
      {!isLoading && filteredMemories.length === 0 && (
        <div className="text-center py-12">
          <Brain className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            No memories yet
          </h3>
          <p className="text-text-muted">
            Start analyzing data to build memory context
          </p>
        </div>
      )}

      <div className="grid gap-4">
        {filteredMemories.map((memory) => (
          <div
            key={memory.id}
            className="card p-5 hover:border-accent-cyan/50 transition-all duration-200"
          >
            <div className="flex items-start justify-between gap-4 mb-3">
              <p className="text-text-primary flex-1">
                {memory.content}
              </p>
              
              <div className="flex items-center gap-2 flex-shrink-0">
                <div
                  className={cn(
                    'px-2 py-1 rounded text-xs font-semibold',
                    memory.importance >= 0.7
                      ? 'bg-accent-green/10 text-accent-green'
                      : memory.importance >= 0.4
                      ? 'bg-accent-yellow/10 text-accent-yellow'
                      : 'bg-text-muted/10 text-text-muted'
                  )}
                >
                  {Math.round(memory.importance * 100)}%
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 text-xs text-text-muted">
              <div className="flex items-center gap-1">
                <Calendar className="w-3.5 h-3.5" />
                <span>{formatTime(memory.created_at)}</span>
              </div>

              {memory.tags.length > 0 && (
                <div className="flex items-center gap-1 flex-wrap">
                  <Tag className="w-3.5 h-3.5" />
                  {memory.tags.slice(0, 3).map((tag, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-full bg-bg-elevated border border-border-subtle"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
