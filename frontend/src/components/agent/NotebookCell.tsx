import { useState } from 'react'
import { cn } from '../../utils/cn'
import { Play, Trash2, Copy, ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { StatusPill, StatusType } from '../shared'

export type CellType = 'code' | 'output' | 'markdown' | 'chart' | 'table' | 'error' | 'plan'

interface NotebookCellProps {
  id: string
  type: CellType
  content: string
  status?: StatusType
  isRunning?: boolean
  stepNumber?: number
  toolName?: string
  onRun?: () => void
  onDelete?: () => void
  className?: string
}

export function NotebookCell({
  id,
  type,
  content,
  status = 'idle',
  isRunning = false,
  stepNumber,
  toolName,
  onRun,
  onDelete,
  className
}: NotebookCellProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)

  const renderContent = () => {
    switch (type) {
      case 'code':
        return (
          <pre className="bg-bg-base p-3 rounded-lg overflow-x-auto text-sm font-mono">
            <code>{content}</code>
          </pre>
        )
      
      case 'output':
        return (
          <div className="bg-bg-base p-3 rounded-lg text-sm">
            <pre className="whitespace-pre-wrap">{content}</pre>
          </div>
        )
      
      case 'markdown':
        return (
          <div className="prose prose-sm max-w-none p-3" dangerouslySetInnerHTML={{ __html: content }} />
        )
      
      case 'chart':
        return (
          <div className="bg-bg-base p-4 rounded-lg">
            <div dangerouslySetInnerHTML={{ __html: content }} />
          </div>
        )
      
      case 'table':
        return (
          <div className="bg-bg-base rounded-lg overflow-x-auto">
            <div dangerouslySetInnerHTML={{ __html: content }} />
          </div>
        )
      
      case 'error':
        return (
          <div className="bg-accent-red/10 border border-accent-red/30 p-3 rounded-lg">
            <p className="text-accent-red text-sm font-mono whitespace-pre-wrap">{content}</p>
          </div>
        )
      
      case 'plan':
        return (
          <div className="bg-accent-blue/5 border border-accent-blue/20 p-4 rounded-lg">
            <div dangerouslySetInnerHTML={{ __html: content }} />
          </div>
        )
      
      default:
        return <p className="text-sm">{content}</p>
    }
  }

  const getHeaderColor = () => {
    switch (type) {
      case 'code': return 'border-l-accent-blue'
      case 'output': return 'border-l-accent-green'
      case 'error': return 'border-l-accent-red'
      case 'plan': return 'border-l-accent-cyan'
      default: return 'border-l-text-muted'
    }
  }

  return (
    <div className={cn(
      'card border-l-4 transition-all duration-200',
      getHeaderColor(),
      isRunning && 'ring-2 ring-accent-cyan/50',
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-border-subtle">
        <div className="flex items-center gap-3">
          {stepNumber && (
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-accent-blue/10 text-accent-blue text-xs font-bold">
              {stepNumber}
            </span>
          )}
          
          <span className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            {type}
          </span>
          
          {toolName && (
            <span className="px-2 py-0.5 rounded-full bg-bg-elevated text-xs text-text-muted border border-border-subtle">
              {toolName}
            </span>
          )}
          
          <StatusPill status={status} size="sm" />
        </div>
        
        <div className="flex items-center gap-2">
          {onRun && type === 'code' && (
            <button
              onClick={onRun}
              disabled={isRunning}
              className="p-1.5 rounded-lg hover:bg-bg-elevated transition-colors disabled:opacity-50"
              title="Run cell"
            >
              {isRunning ? (
                <Loader2 className="w-4 h-4 animate-spin text-accent-cyan" />
              ) : (
                <Play className="w-4 h-4 text-accent-green" />
              )}
            </button>
          )}
          
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg hover:bg-bg-elevated transition-colors"
            title={isCollapsed ? 'Expand' : 'Collapse'}
          >
            {isCollapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          
          {onDelete && (
            <button
              onClick={onDelete}
              className="p-1.5 rounded-lg hover:bg-accent-red/10 transition-colors"
              title="Delete cell"
            >
              <Trash2 className="w-4 h-4 text-accent-red" />
            </button>
          )}
        </div>
      </div>
      
      {/* Content */}
      {!isCollapsed && (
        <div className="p-4">
          {renderContent()}
        </div>
      )}
    </div>
  )
}
