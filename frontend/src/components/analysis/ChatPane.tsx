import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { useAgentStore } from '../../store/useAgentStore'
import { useRunAnalysis } from '../../api/analysis'
import { Send, Loader2, FileText } from 'lucide-react'

export function ChatPane() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState<'analysis_only' | 'analysis_ml' | 'analysis_ml_notebook'>('analysis_only')
  
  const { currentDataset, domain } = useAppStore()
  const { status, traceSteps, finalResponse, error, reset } = useAgentStore()
  const runAnalysis = useRunAnalysis()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || !currentDataset) return

    reset()
    
    await runAnalysis.mutateAsync({
      query,
      dataset_hash: currentDataset.hash,
      domain,
      mode,
    })
  }

  return (
    <div className="h-full flex flex-col">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {traceSteps.length === 0 && !finalResponse && (
          <div className="text-center text-text-muted mt-20">
            <p className="mb-2">Enter an instruction to start analysis</p>
            <p className="text-sm">Example: "analyze and find trends"</p>
          </div>
        )}

        {/* Trace Steps */}
        {traceSteps.map((step, idx) => (
          <div key={step.id} className="bg-bg-elevated rounded-lg p-3">
            <div className="flex items-center gap-2 text-sm text-text-muted mb-1">
              <span className="text-accent-blue">{step.agent}</span>
              <span>→</span>
              <span>{step.action}</span>
            </div>
            <p className="text-sm text-text-primary">{step.output}</p>
          </div>
        ))}

        {/* Final Response */}
        {finalResponse && (
          <div className="bg-accent-blue/10 border border-accent-blue/20 rounded-lg p-4">
            <p className="text-text-primary whitespace-pre-wrap">{finalResponse}</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-accent-red/10 border border-accent-red/20 rounded-lg p-4 text-accent-red">
            {error}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border-subtle">
        {/* Mode Selection */}
        <div className="flex gap-2 mb-3">
          {[
            { key: 'analysis_only', label: 'Analysis Only' },
            { key: 'analysis_ml', label: 'Analysis + ML' },
            { key: 'analysis_ml_notebook', label: 'Analysis + ML + Notebook' },
          ].map((m) => (
            <button
              key={m.key}
              onClick={() => setMode(m.key as any)}
              className={`px-3 py-1 text-xs rounded-full transition-colors ${
                mode === m.key
                  ? 'bg-accent-blue text-white'
                  : 'bg-bg-elevated text-text-muted hover:text-text-primary'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Input */}
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={currentDataset ? "Enter your analysis instruction..." : "Load a dataset first..."}
            disabled={!currentDataset || status === 'running'}
            className="flex-1 input"
          />
          <button
            type="submit"
            disabled={!currentDataset || status === 'running' || !query.trim()}
            className="btn-primary px-4"
          >
            {status === 'running' ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </form>
      </div>
    </div>
  )
}
