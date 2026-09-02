import { useState } from 'react'
import { cn } from '../../utils/cn'
import { DataSourceSelector, DataSourceType } from './DataSourceSelector'
import { Play, Loader2, Sparkles } from 'lucide-react'

interface InputPanelProps {
  onRun: (instruction: string, dataSource: { type: DataSourceType; data: any }) => void
  isRunning?: boolean
  className?: string
}

export function InputPanel({ onRun, isRunning = false, className }: InputPanelProps) {
  const [instruction, setInstruction] = useState('')
  const [dataSource, setDataSource] = useState<{ type: DataSourceType; data: any } | null>(null)

  const handleSourceSelected = (type: DataSourceType, data: any) => {
    setDataSource({ type, data })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (instruction.trim() && dataSource) {
      onRun(instruction.trim(), dataSource)
      setInstruction('')
    }
  }

  const canRun = instruction.trim() && dataSource && !isRunning

  return (
    <div className={cn('space-y-4', className)}>
      {/* Instruction Input */}
      <div className="card p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-accent-cyan" />
          Analysis Instruction
        </h3>
        
        <form onSubmit={handleSubmit}>
          <textarea
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            placeholder="e.g., Analyze this dataset and find key trends, build a prediction model..."
            className="textarea w-full text-sm mb-3"
            rows={4}
            required
          />
          
          <button
            type="submit"
            disabled={!canRun}
            className="btn-primary w-full flex items-center justify-center gap-2 text-sm"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Running Analysis...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Analysis
              </>
            )}
          </button>
        </form>
      </div>

      {/* Data Source Selector */}
      <DataSourceSelector onSourceSelected={handleSourceSelected} />

      {/* Data Source Status */}
      {dataSource && (
        <div className="card p-3 bg-accent-green/5 border-accent-green/30">
          <p className="text-xs text-text-muted mb-1">Selected Source:</p>
          <p className="text-sm text-text-primary">
            {dataSource.type === 'upload' && `File: ${(dataSource.data.file as File)?.name}`}
            {dataSource.type === 'url' && `URL: ${dataSource.data.url}`}
            {dataSource.type === 'kaggle' && `Kaggle: ${dataSource.data.query}`}
          </p>
        </div>
      )}
    </div>
  )
}
