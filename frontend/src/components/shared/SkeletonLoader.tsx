import { cn } from '../../utils/cn'

interface SkeletonLoaderProps {
  variant?: 'text' | 'card' | 'chart' | 'table' | 'circle'
  lines?: number
  className?: string
}

function TextSkeleton({ lines = 1, className }: { lines?: number; className?: string }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className={cn(
            'h-4 bg-bg-elevated rounded animate-pulse',
            i === lines - 1 && 'w-3/4',
            className
          )}
        />
      ))}
    </div>
  )
}

function CardSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('card p-4 space-y-3', className)}>
      <div className="h-4 bg-bg-elevated rounded w-1/3 animate-pulse" />
      <div className="h-8 bg-bg-elevated rounded w-2/3 animate-pulse" />
      <div className="h-4 bg-bg-elevated rounded w-1/2 animate-pulse" />
    </div>
  )
}

function ChartSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('card p-4', className)}>
      <div className="h-4 bg-bg-elevated rounded w-1/4 mb-4 animate-pulse" />
      <div className="h-64 bg-bg-elevated rounded animate-pulse" />
    </div>
  )
}

function TableSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('card overflow-hidden', className)}>
      <div className="p-4 border-b border-border-subtle">
        <div className="h-4 bg-bg-elevated rounded w-1/4 animate-pulse" />
      </div>
      <div className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4">
            {Array.from({ length: 4 }).map((_, j) => (
              <div
                key={j}
                className="h-4 bg-bg-elevated rounded flex-1 animate-pulse"
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}

function CircleSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn('w-16 h-16 rounded-full bg-bg-elevated animate-pulse', className)} />
  )
}

export function SkeletonLoader({ 
  variant = 'text', 
  lines = 1, 
  className 
}: SkeletonLoaderProps) {
  switch (variant) {
    case 'text':
      return <TextSkeleton lines={lines} className={className} />
    case 'card':
      return <CardSkeleton className={className} />
    case 'chart':
      return <ChartSkeleton className={className} />
    case 'table':
      return <TableSkeleton className={className} />
    case 'circle':
      return <CircleSkeleton className={className} />
    default:
      return <TextSkeleton lines={lines} className={className} />
  }
}
