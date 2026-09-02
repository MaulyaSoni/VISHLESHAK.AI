import { cn } from '../../utils/cn'
import { CheckCircle, Circle, Loader2, AlertCircle } from 'lucide-react'

export type PlanStepStatus = 'pending' | 'running' | 'completed' | 'failed'

interface AgentPlanStepProps {
  stepNumber: number
  title: string
  tool?: string
  status: PlanStepStatus
  description?: string
  className?: string
}

const statusConfig = {
  pending: {
    icon: Circle,
    color: 'text-text-muted',
    bg: 'bg-bg-elevated'
  },
  running: {
    icon: Loader2,
    color: 'text-accent-cyan animate-spin',
    bg: 'bg-accent-cyan/10'
  },
  completed: {
    icon: CheckCircle,
    color: 'text-accent-green',
    bg: 'bg-accent-green/10'
  },
  failed: {
    icon: AlertCircle,
    color: 'text-accent-red',
    bg: 'bg-accent-red/10'
  }
}

export function AgentPlanStep({
  stepNumber,
  title,
  tool,
  status,
  description,
  className
}: AgentPlanStepProps) {
  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <div className={cn(
      'flex items-start gap-3 p-3 rounded-lg transition-all duration-200',
      status === 'running' && 'bg-accent-cyan/5',
      className
    )}>
      {/* Step Number & Status Icon */}
      <div className="flex-shrink-0 relative">
        <div className={cn(
          'w-8 h-8 rounded-full flex items-center justify-center',
          config.bg
        )}>
          <Icon className={cn('w-4 h-4', config.color)} />
        </div>
        <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-accent-blue text-white text-xs flex items-center justify-center font-bold">
          {stepNumber}
        </span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="text-sm font-semibold text-text-primary truncate">
            {title}
          </h4>
          {tool && (
            <span className="px-2 py-0.5 rounded-full bg-bg-elevated text-xs text-text-muted border border-border-subtle flex-shrink-0">
              {tool}
            </span>
          )}
        </div>
        
        {description && (
          <p className="text-xs text-text-muted line-clamp-2">
            {description}
          </p>
        )}
      </div>
    </div>
  )
}
