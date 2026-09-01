import { cn } from '../../utils/cn'
import { ChevronDown, ChevronRight, Brain, Tool, Eye } from 'lucide-react'
import { useState } from 'react'

export interface ReasoningStep {
  type: 'thought' | 'action' | 'observation'
  content: string
  tool?: string
}

interface ReasoningTraceProps {
  steps: ReasoningStep[]
  className?: string
  defaultExpanded?: boolean
}

const stepConfig = {
  thought: {
    icon: Brain,
    color: 'text-accent-blue',
    bg: 'bg-accent-blue/5',
    border: 'border-accent-blue/20',
    label: 'Thought'
  },
  action: {
    icon: Tool,
    color: 'text-accent-cyan',
    bg: 'bg-accent-cyan/5',
    border: 'border-accent-cyan/20',
    label: 'Action'
  },
  observation: {
    icon: Eye,
    color: 'text-accent-green',
    bg: 'bg-accent-green/5',
    border: 'border-accent-green/20',
    label: 'Observation'
  }
}

export function ReasoningTrace({ 
  steps, 
  className,
  defaultExpanded = false
}: ReasoningTraceProps) {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(
    defaultExpanded ? new Set(steps.map((_, i) => i)) : new Set()
  )

  const toggleStep = (index: number) => {
    const newExpanded = new Set(expandedSteps)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedSteps(newExpanded)
  }

  if (steps.length === 0) {
    return null
  }

  return (
    <div className={cn('space-y-2', className)}>
      <h4 className="text-xs font-semibold text-text-muted uppercase tracking-wider mb-3">
        Reasoning Trace
      </h4>

      {steps.map((step, index) => {
        const config = stepConfig[step.type]
        const Icon = config.icon
        const isExpanded = expandedSteps.has(index)

        return (
          <div
            key={index}
            className={cn(
              'rounded-lg border transition-all duration-200',
              config.bg,
              config.border
            )}
          >
            <button
              onClick={() => toggleStep(index)}
              className="w-full flex items-center gap-3 p-3 text-left"
            >
              <Icon className={cn('w-4 h-4 flex-shrink-0', config.color)} />
              
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={cn('text-xs font-semibold', config.color)}>
                    {config.label}
                  </span>
                  {step.tool && (
                    <span className="px-2 py-0.5 rounded-full bg-bg-elevated text-xs text-text-muted border border-border-subtle">
                      {step.tool}
                    </span>
                  )}
                </div>
                
                {!isExpanded && (
                  <p className="text-xs text-text-muted mt-1 truncate">
                    {step.content}
                  </p>
                )}
              </div>

              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-text-muted flex-shrink-0" />
              ) : (
                <ChevronRight className="w-4 h-4 text-text-muted flex-shrink-0" />
              )}
            </button>

            {isExpanded && (
              <div className="px-3 pb-3 pl-10">
                <p className="text-sm text-text-primary whitespace-pre-wrap">
                  {step.content}
                </p>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
