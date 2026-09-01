import { cn } from '../../utils/cn'
import { MessageSquare, Clock, Trash2 } from 'lucide-react'

export interface Conversation {
  id: string
  title: string
  messageCount: number
  lastMessage: Date
  isActive?: boolean
}

interface ConversationHistoryProps {
  conversations: Conversation[]
  onSelect: (id: string) => void
  onDelete?: (id: string) => void
  className?: string
}

export function ConversationHistory({
  conversations,
  onSelect,
  onDelete,
  className
}: ConversationHistoryProps) {
  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    const days = Math.floor(hours / 24)

    if (hours < 1) return 'Just now'
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString()
  }

  if (conversations.length === 0) {
    return (
      <div className={cn('p-4 text-center', className)}>
        <MessageSquare className="w-8 h-8 text-text-muted mx-auto mb-2" />
        <p className="text-sm text-text-muted">No conversations yet</p>
      </div>
    )
  }

  return (
    <div className={cn('space-y-1', className)}>
      {conversations.map((conv) => (
        <div
          key={conv.id}
          className={cn(
            'group flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-all duration-200',
            conv.isActive
              ? 'bg-accent-blue/10 border-l-2 border-accent-blue'
              : 'hover:bg-bg-elevated border-l-2 border-transparent'
          )}
          onClick={() => onSelect(conv.id)}
        >
          <MessageSquare
            className={cn(
              'w-4 h-4 flex-shrink-0 mt-0.5',
              conv.isActive ? 'text-accent-blue' : 'text-text-muted'
            )}
          />

          <div className="flex-1 min-w-0">
            <h4
              className={cn(
                'text-sm font-medium truncate',
                conv.isActive ? 'text-accent-blue' : 'text-text-primary'
              )}
            >
              {conv.title}
            </h4>

            <div className="flex items-center gap-2 mt-1">
              <Clock className="w-3 h-3 text-text-muted" />
              <span className="text-xs text-text-muted">
                {formatTime(conv.lastMessage)}
              </span>
              <span className="text-xs text-text-muted">•</span>
              <span className="text-xs text-text-muted">
                {conv.messageCount} messages
              </span>
            </div>
          </div>

          {onDelete && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete(conv.id)
              }}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-accent-red/10 transition-all"
            >
              <Trash2 className="w-3.5 h-3.5 text-accent-red" />
            </button>
          )}
        </div>
      ))}
    </div>
  )
}
