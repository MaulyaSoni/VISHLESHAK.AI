import { useState, useEffect, useCallback } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { HeroHeader } from '../layout/HeroHeader'
import { FileUploader } from '../shared/FileUploader'
import { 
  Bot, 
  Send, 
  Settings, 
  RefreshCw, 
  StopCircle,
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  BarChart3,
  Brain,
  BookOpen,
  Code,
  Download
} from 'lucide-react'
import { API_BASE_URL } from '@/api/client'

interface AgentStep {
  step: string
  status: 'pending' | 'running' | 'done' | 'error'
}

interface AgentReport {
  metadata?: {
    rows?: number
    cols?: number
    source?: string
  }
  insights?: {
    executive_summary?: string
    key_findings?: string[]
    recommendations?: string[]
    anomalies_or_risks?: string[]
  }
  charts?: Array<{
    title: string
    type: string
    html_path?: string
    png_path?: string
    image_data?: string  // base64 encoded image
    interpretation?: string
  }>
  ml_results?: {
    task_type?: string
    target_col?: string
    metrics?: Record<string, number>
    feature_importance?: Record<string, number>
  }
  notebook_path?: string
}

const MODES = [
  { key: 'analysis_only', label: 'Analysis Only', desc: 'Data analysis without ML' },
  { key: 'analysis_ml', label: 'Analysis + ML Model', desc: 'Analysis with machine learning' },
  { key: 'analysis_ml_notebook', label: 'Analysis + ML + Notebook', desc: 'Full pipeline with Jupyter notebook' },
]

const TABS = [
  { key: 'summary', label: '📋 Summary', icon: FileText },
  { key: 'charts', label: '📈 Charts', icon: BarChart3 },
  { key: 'ml', label: '🤖 ML Results', icon: Brain },
  { key: 'notebook', label: '📓 Notebook', icon: BookOpen },
  { key: 'raw', label: '📄 Raw JSON', icon: Code },
]

export function DataAgentMode() {
  const { currentDataset, setCurrentDataset, addDataset } = useAppStore()
  const [instruction, setInstruction] = useState('')
  const [agentMode, setAgentMode] = useState('analysis_ml')
  const [isRunning, setIsRunning] = useState(false)
  const [steps, setSteps] = useState<AgentStep[]>([])
  const [report, setReport] = useState<AgentReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [progress, setProgress] = useState(0)
  const [activeTab, setActiveTab] = useState('summary')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [stepDelay, setStepDelay] = useState(2)
  const [maxSteps, setMaxSteps] = useState(15)
  const [isUploading, setIsUploading] = useState(false)

  // Poll for progress when running
  useEffect(() => {
    if (!isRunning) return

    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/agent/progress`)
        if (response.ok) {
          const data = await response.json()
          setSteps(data.steps || [])
          setProgress(data.progress || 0)
          
          if (data.status === 'done') {
            setIsRunning(false)
            setReport(data.report)
          } else if (data.status === 'error') {
            setIsRunning(false)
            setError(data.error || 'Unknown error')
          }
        }
      } catch (e) {
        // Ignore polling errors
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [isRunning])

  const handleFileUpload = async (file: File) => {
    setIsUploading(true)
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) throw new Error('Upload failed')
      
      const result = await response.json()
      const dataset = {
        hash: result.dataset_hash,
        filename: result.filename,
        rows: result.rows,
        cols: result.cols,
        numericCount: result.numeric_count || 0,
        categoricalCount: result.categorical_count || 0,
        missingPct: result.missing_pct || 0,
        meta: result.meta || {},
      }
      
      addDataset(dataset)
      setCurrentDataset(dataset)
      
      // Auto-populate instruction with filename
      if (!instruction) {
        setInstruction(`Analyze ${result.filename} and find insights`)
      }
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setIsUploading(false)
    }
  }

  const handleRunAgent = async () => {
    if (!instruction.trim()) return
    
    setIsRunning(true)
    setError(null)
    setReport(null)
    setSteps([])
    setProgress(0)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/agent/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          instruction: instruction.trim(),
          mode: agentMode,
          dataset_hash: currentDataset?.hash,
          step_delay: stepDelay,
          max_steps: maxSteps,
        }),
      })
      
      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.error || 'Failed to start agent')
      }
    } catch (error) {
      setIsRunning(false)
      setError(error instanceof Error ? error.message : 'Unknown error')
    }
  }

  const handleStopAgent = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/agent/stop`, { method: 'POST' })
      setIsRunning(false)
    } catch (e) {
      // Ignore
    }
  }

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'done': return <CheckCircle className="w-4 h-4 text-accent-green" />
      case 'running': return <RefreshCw className="w-4 h-4 text-accent-cyan animate-spin" />
      case 'error': return <AlertCircle className="w-4 h-4 text-accent-red" />
      default: return <Clock className="w-4 h-4 text-text-muted" />
    }
  }

  return (
    <div className="h-full overflow-auto">
      {!report ? (
        // Input view
        <div className="max-w-6xl mx-auto p-6">
          <HeroHeader />
          
          <div className="grid grid-cols-[35%_65%] gap-6 mt-8">
            {/* Left Panel - Input */}
            <div className="space-y-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Bot className="w-6 h-6 text-accent-blue" />
                Data Agent
              </h2>
              
              <div>
                <label className="block text-sm font-medium mb-2">What do you want to analyze?</label>
                <textarea
                  value={instruction}
                  onChange={(e) => setInstruction(e.target.value)}
                  placeholder="analyze Insurance.csv and find trends / train a model to predict Amount / download https://... and summarize"
                  className="textarea w-full"
                  rows={5}
                />
              </div>

              {/* Mode Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">Mode</label>
                <div className="space-y-2">
                  {MODES.map(({ key, label, desc }) => (
                    <label 
                      key={key}
                      className={`mode-radio ${agentMode === key ? 'active' : ''}`}
                    >
                      <input
                        type="radio"
                        name="agentMode"
                        value={key}
                        checked={agentMode === key}
                        onChange={(e) => setAgentMode(e.target.value)}
                        className="w-4 h-4 accent-accent-blue"
                      />
                      <div>
                        <div className="text-sm font-medium">{label}</div>
                        <div className="text-xs text-text-muted">{desc}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>

              {/* File Upload */}
              <div>
                <label className="block text-sm font-medium mb-2">Upload CSV (optional)</label>
                <FileUploader 
                  onUpload={handleFileUpload} 
                  isLoading={isUploading}
                  accept=".csv"
                />
              </div>

              {/* Advanced Settings */}
              <div>
                <button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="flex items-center gap-2 text-text-muted hover:text-text-primary"
                >
                  <Settings className="w-4 h-4" />
                  <span className="text-sm">Advanced</span>
                </button>
                
                {showAdvanced && (
                  <div className="mt-3 space-y-3 p-3 bg-bg-elevated rounded-lg">
                    <div>
                      <label className="text-xs text-text-muted">Step Delay (seconds)</label>
                      <input
                        type="range"
                        min={1}
                        max={5}
                        value={stepDelay}
                        onChange={(e) => setStepDelay(Number(e.target.value))}
                        className="w-full"
                      />
                      <span className="text-sm">{stepDelay}s</span>
                    </div>
                    <div>
                      <label className="text-xs text-text-muted">Max Loop Steps</label>
                      <input
                        type="range"
                        min={10}
                        max={25}
                        value={maxSteps}
                        onChange={(e) => setMaxSteps(Number(e.target.value))}
                        className="w-full"
                      />
                      <span className="text-sm">{maxSteps}</span>
                    </div>
                  </div>
                )}
              </div>

              {/* Run Button */}
              <button
                onClick={handleRunAgent}
                disabled={!instruction.trim() || isRunning}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {isRunning ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    🚀 Run Agent
                  </>
                )}
              </button>
            </div>

            {/* Right Panel - Output */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-accent-blue" />
                Output
              </h3>
              
              {!isRunning && steps.length === 0 ? (
                // Empty state
                <div className="card p-8 text-center">
                  <div className="text-5xl mb-4">🤖</div>
                  <p className="text-text-muted">
                    Enter an instruction and click <b>Run Agent</b> to start analysis.
                  </p>
                  <p className="text-sm text-text-muted mt-2">
                    Example: "analyze Insurance.csv and find trends"
                  </p>
                </div>
              ) : (
                // Progress view
                <div className="card p-6">
                  <h4 className="font-semibold mb-4 flex items-center gap-2">
                    <RefreshCw className={`w-5 h-5 ${isRunning ? 'animate-spin text-accent-cyan' : 'text-accent-green'}`} />
                    {isRunning ? 'Agent Running...' : 'Agent Complete'}
                  </h4>
                  
                  {/* Progress Bar */}
                  <div className="mb-6">
                    <div className="h-2 bg-bg-elevated rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-accent-blue to-accent-cyan transition-all duration-500"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <p className="text-sm text-text-muted mt-2">
                      Step {Math.round(progress / 10)}/10: Processing...
                    </p>
                  </div>

                  {/* Steps */}
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-text-muted mb-2">Progress Steps:</p>
                    {steps.length === 0 ? (
                      <p className="text-sm text-text-muted">⏳ Initializing...</p>
                    ) : (
                      steps.map((step, idx) => (
                        <div key={idx} className="step-item">
                          {getStepIcon(step.status)}
                          <span className={`text-sm ${
                            step.status === 'done' ? 'text-accent-green' :
                            step.status === 'running' ? 'text-accent-cyan' :
                            'text-text-muted'
                          }`}>
                            {step.status === 'done' ? '✅' : step.status === 'running' ? '🔄' : '⏳'} {step.step}
                          </span>
                        </div>
                      ))
                    )}
                  </div>

                  {/* Error */}
                  {error && (
                    <div className="mt-4 p-3 bg-accent-red/10 border border-accent-red/30 rounded-lg">
                      <p className="text-accent-red text-sm">❌ {error}</p>
                    </div>
                  )}

                  {/* Actions */}
                  {isRunning && (
                    <div className="mt-4 flex gap-2">
                      <button
                        onClick={handleStopAgent}
                        className="btn-secondary flex items-center gap-2 text-sm"
                      >
                        <StopCircle className="w-4 h-4" />
                        Stop Agent
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        // Results view
        <div className="max-w-7xl mx-auto p-6">
          {/* Results Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <CheckCircle className="w-8 h-8 text-accent-green" />
              <div>
                <h2 className="text-2xl font-bold">Analysis Complete</h2>
                <p className="text-text-muted text-sm">{instruction}</p>
              </div>
            </div>
            <button
              onClick={() => {
                setReport(null)
                setSteps([])
                setProgress(0)
              }}
              className="btn-primary"
            >
              🔄 New Analysis
            </button>
          </div>

          {/* Metric Cards */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="metric-card">
              <div className="metric-value">{report.metadata?.rows || 'N/A'}</div>
              <div className="metric-label">📊 Rows</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{report.metadata?.cols || 'N/A'}</div>
              <div className="metric-label">📋 Columns</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">{report.charts?.length || 0}</div>
              <div className="metric-label">📈 Charts</div>
            </div>
            <div className="metric-card">
              <div className="metric-value">
                {report.ml_results?.metrics?.r2_score 
                  ? report.ml_results.metrics.r2_score.toFixed(3)
                  : report.ml_results?.metrics?.accuracy 
                    ? report.ml_results.metrics.accuracy.toFixed(3)
                    : 'N/A'}
              </div>
              <div className="metric-label">🎯 Model Score</div>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 border-b border-border-subtle mb-6">
            {TABS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setActiveTab(key)}
                className={`tab ${activeTab === key ? 'active' : ''}`}
              >
                {label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="min-h-[400px]">
            {activeTab === 'summary' && (
              <div className="space-y-4">
                {report.insights?.executive_summary && (
                  <div className="card p-5">
                    <h4 className="font-semibold mb-3">📝 Executive Summary</h4>
                    <p className="text-text-primary leading-relaxed">{report.insights.executive_summary}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  {report.insights?.key_findings && report.insights.key_findings.length > 0 && (
                    <div className="card p-5">
                      <h4 className="font-semibold mb-3">🔍 Key Findings</h4>
                      <ul className="space-y-2">
                        {report.insights.key_findings.map((f, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-accent-green">✓</span>
                            <span>{f}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {report.insights?.recommendations && report.insights.recommendations.length > 0 && (
                    <div className="card p-5">
                      <h4 className="font-semibold mb-3">💡 Recommendations</h4>
                      <ul className="space-y-2">
                        {report.insights.recommendations.map((r, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-accent-blue">→</span>
                            <span>{r}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'charts' && (
              <div className="space-y-4">
                {report.charts && report.charts.length > 0 ? (
                  report.charts.map((chart, i) => (
                    <div key={i} className="card p-4">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-medium">{chart.title} <span className="text-text-muted text-sm">({chart.type})</span></h4>
                        <div className="flex gap-2">
                          {chart.image_data && (
                            <button 
                              onClick={() => {
                                // Download PNG from base64
                                const link = document.createElement('a')
                                link.download = `${chart.title.replace(/\s+/g, '_')}.png`
                                link.href = chart.image_data!
                                link.click()
                              }}
                              className="btn-ghost text-xs flex items-center gap-1"
                            >
                              <Download className="w-3 h-3" />
                              PNG
                            </button>
                          )}
                        </div>
                      </div>
                      <div className="h-80 bg-bg-elevated rounded-lg flex items-center justify-center border border-border-subtle overflow-hidden">
                        {chart.image_data ? (
                          <img 
                            src={chart.image_data} 
                            alt={chart.title}
                            className="max-w-full max-h-full object-contain"
                          />
                        ) : (
                          <div className="text-center">
                            <BarChart3 className="w-12 h-12 text-accent-blue mx-auto mb-2" />
                            <p className="text-text-muted">{chart.title}</p>
                            <p className="text-xs text-text-muted mt-1">Type: {chart.type}</p>
                          </div>
                        )}
                      </div>
                      {chart.interpretation && (
                        <p className="text-sm text-text-muted mt-3">💡 {chart.interpretation}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-text-muted text-center py-8">No charts generated</p>
                )}
              </div>
            )}

            {activeTab === 'ml' && (
              <div className="card p-5">
                {report.ml_results ? (
                  <div className="space-y-4">
                    <p><strong>Task:</strong> {report.ml_results.task_type}</p>
                    <p><strong>Target:</strong> {report.ml_results.target_col}</p>
                    {report.ml_results.metrics && (
                      <div className="grid grid-cols-3 gap-4">
                        {Object.entries(report.ml_results.metrics).map(([k, v]) => (
                          <div key={k} className="metric-card">
                            <div className="metric-value">{typeof v === 'number' ? v.toFixed(3) : v}</div>
                            <div className="metric-label">{k}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-text-muted">No ML results - run with Analysis + ML Model mode</p>
                )}
              </div>
            )}

            {activeTab === 'notebook' && (
              <div className="card p-5">
                {report.notebook_path ? (
                  <div>
                    <p className="text-accent-green mb-2">✅ Notebook generated</p>
                    <p className="text-text-muted text-sm mb-4">{report.notebook_path.split(/[\\/]/).pop()}</p>
                    <button 
                      onClick={async () => {
                        // Download from backend
                        try {
                          const filename = report.notebook_path!.split(/[\\/]/).pop()!
                          const response = await fetch(`${API_BASE_URL}/api/agent/notebook/${filename}`)
                          if (response.ok) {
                            const blob = await response.blob()
                            const url = URL.createObjectURL(blob)
                            const a = document.createElement('a')
                            a.href = url
                            a.download = filename
                            document.body.appendChild(a)
                            a.click()
                            document.body.removeChild(a)
                            URL.revokeObjectURL(url)
                          } else {
                            // Fallback: create notebook from report data
                            const notebook = {
                              cells: [
                                { cell_type: 'markdown', source: [`# Analysis Notebook\n\nGenerated for: ${instruction}\n\nDate: ${new Date().toLocaleString()}`] },
                                { cell_type: 'markdown', source: ['## Executive Summary\n\n' + (report.insights?.executive_summary || 'No summary available')] },
                                { cell_type: 'code', execution_count: 1, source: ['import pandas as pd\nimport numpy as np\nimport matplotlib.pyplot as plt'], outputs: [] },
                                { cell_type: 'code', execution_count: 2, source: ['# Load your dataset\n# df = pd.read_csv("your_data.csv")\n# df.head()'], outputs: [] },
                              ],
                              metadata: { kernelspec: { display_name: 'Python 3', language: 'python', name: 'python3' } },
                              nbformat: 4,
                              nbformat_minor: 4
                            }
                            const blob = new Blob([JSON.stringify(notebook, null, 2)], { type: 'application/json' })
                            const url = URL.createObjectURL(blob)
                            const a = document.createElement('a')
                            a.href = url
                            a.download = filename
                            document.body.appendChild(a)
                            a.click()
                            document.body.removeChild(a)
                            URL.revokeObjectURL(url)
                          }
                        } catch (e) {
                          console.error('Download failed:', e)
                        }
                      }}
                      className="btn-primary flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download .ipynb
                    </button>
                  </div>
                ) : (
                  <p className="text-text-muted">No notebook generated - run with 'Analysis + ML + Notebook' mode</p>
                )}
              </div>
            )}

            {activeTab === 'raw' && (
              <div className="card p-5">
                <pre className="bg-bg-elevated p-4 rounded-lg overflow-auto text-xs max-h-[600px]">
                  {JSON.stringify(report, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
