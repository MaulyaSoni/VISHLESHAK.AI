import { cn } from '../../utils/cn'
import { NotebookCell, CellType } from './NotebookCell'
import { AgentPlanStep, PlanStepStatus } from './AgentPlanStep'
import { StatusType } from '../shared'
import { Database, ArrowRight, Sparkles } from 'lucide-react'

export interface NotebookCellData {
  id: string
  type: CellType
  content: string
  status?: StatusType
  isRunning?: boolean
  stepNumber?: number
  toolName?: string
}

export interface PlanStepData {
  stepNumber: number
  title: string
  tool?: string
  status: PlanStepStatus
  description?: string
}

interface NotebookCanvasProps {
  cells: NotebookCellData[]
  planSteps?: PlanStepData[]
  showEmptyState?: boolean
  className?: string
}

export function NotebookCanvas({
  cells,
  planSteps,
  showEmptyState = true,
  className
}: NotebookCanvasProps) {
  if (showEmptyState && cells.length === 0 && (!planSteps || planSteps.length === 0)) {
    return (
      <div className={cn(
        'flex flex-col items-center justify-center h-full min-h-[400px] p-8',
        className
      )}>
        <div className="text-center max-w-md">
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-accent-blue/10 mb-6">
            <Database className="w-10 h-10 text-accent-blue" />
          </div>
          
          <h3 className="text-xl font-semibold text-text-primary mb-2">
            Ready to Analyze
          </h3>
          
          <p className="text-text-muted mb-6">
            Select a data source and provide an analysis instruction to get started.
            The agent will automatically plan and execute the analysis.
          </p>
          
          <div className="space-y-3 text-left">
            <div className="flex items-start gap-3 p-3 rounded-lg bg-bg-surface border border-border-subtle">
              <ArrowRight className="w-5 h-5 text-accent-cyan flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-text-primary">Upload Data</p>
                <p className="text-xs text-text-muted">CSV, Excel files or Kaggle datasets</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 rounded-lg bg-bg-surface border border-border-subtle">
              <Sparkles className="w-5 h-5 text-accent-green flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-text-primary">AI Analysis</p>
                <p className="text-xs text-text-muted">Automated EDA, insights, and predictions</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className={cn('space-y-4 p-4', className)}>
      {/* Plan Steps */}
      {planSteps && planSteps.length > 0 && (
        <div className="card p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Execution Plan
          </h3>
          <div className="space-y-2">
            {planSteps.map((step) => (
              <AgentPlanStep
                key={step.stepNumber}
                stepNumber={step.stepNumber}
                title={step.title}
                tool={step.tool}
                status={step.status}
                description={step.description}
              />
            ))}
          </div>
        </div>
      )}

      {/* Notebook Cells */}
      <div className="space-y-3">
        {cells.map((cell) => (
          <NotebookCell
            key={cell.id}
            id={cell.id}
            type={cell.type}
            content={cell.content}
            status={cell.status}
            isRunning={cell.isRunning}
            stepNumber={cell.stepNumber}
            toolName={cell.toolName}
          />
        ))}
      </div>
    </div>
  )
}
