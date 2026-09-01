import { cn } from '../../utils/cn'

export type StatusType = 'idle' | 'running' | 'done' | 'error' | 'cancelled'

interface StatusPillProps {
  status: StatusType
  label?: string
  size?: 'sm' | 'md' | 'lg'
  className?: string
}

const statusConfig = {
  idle: {
    color: 'bg-bg-elevated text-text-muted border-border-subtle',
    dot: 'bg-text-muted',
    label: 'Idle'
  },
  running: {
    color: 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30',
    dot: 'bg-accent-cyan animate-pulse',
    label: 'Running'
  },
  done: {
    color: 'bg-accent-green/10 text-accent-green border-accent-green/30',
    dot: 'bg-accent-green',
    label: 'Done'
  },
  error: {
    color: 'bg-accent-red/10 text-accent-red border-accent-red/30',
    dot: 'bg-accent-red',
    label: 'Error'
  },
  cancelled: {
    color: 'bg-text-muted/10 text-text-muted border-text-muted/30',
    dot: 'bg-text-muted',
    label: 'Cancelled'
  }
}

const sizeConfig = {
  sm: 'px-2 py-0.5 text-xs',
  md: 'px-3 py-1 text-sm',
  lg: 'px-4 py-1.5 text-base'
}

export function StatusPill({ status, label, size = 'md', className }: StatusPillProps) {
  const config = statusConfig[status]
  
  return (
    <span
      className={cn(
        'inline-flex items-center gap-2 rounded-full border font-medium',
        config.color,
        sizeConfig[size],
        className
      )}
    >
      <span className={cn('w-2 h-2 rounded-full', config.dot)} />
      {label || config.label}
    </span>
  )
}
