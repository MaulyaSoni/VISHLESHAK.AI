import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { HeroHeader } from '../layout/HeroHeader'
import { FileUploader } from '../shared/FileUploader'
import { DataPreview } from '../shared/DataPreview'
import { AnalysisResults } from '../shared/AnalysisResults'
import { 
  BarChart3, 
  Sparkles, 
  ChevronDown, 
  ChevronUp,
  RefreshCw,
  Database
} from 'lucide-react'
import { API_BASE_URL } from '@/api/client'

// Feature cards like app.py
const FEATURES = [
  { icon: '📊', title: 'Deep Analysis', desc: 'Statistical insights, pattern detection & AI summaries' },
  { icon: '💬', title: 'RAG Chatbot', desc: 'Data-aware Q&A with knowledge base & tools' },
  { icon: '📈', title: 'Smart Charts', desc: 'Intelligent visualisations chosen for your data' },
  { icon: '🧠', title: 'Memory System', desc: 'LSTM-like multi-tiered conversation memory' },
  { icon: '🎯', title: 'Quality Scoring', desc: '8-dimension response evaluation & learning' },
  { icon: '⚡', title: 'Agentic Tools', desc: 'Python REPL, calculator, export & more' },
]

export function AnalysisMode() {
  const { 
    currentDataset, 
    addDataset, 
    setCurrentDataset,
    setAnalysisResult,
    setChartsCache,
    analysisResult,
    useAgentMode,
    domain
  } = useAppStore()
  
  const [isUploading, setIsUploading] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isGeneratingCharts, setIsGeneratingCharts] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [showVisuals, setShowVisuals] = useState(false)

  const handleFileUpload = async (file: File) => {
    setIsUploading(true)
    setUploadError(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/upload`, {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Upload failed')
      }
      
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
      setShowPreview(true)
    } catch (error) {
      console.error('Upload failed:', error)
      setUploadError(error instanceof Error ? error.message : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  const handleAnalyze = async () => {
    if (!currentDataset) return
    
    setIsAnalyzing(true)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_hash: currentDataset.hash,
          use_agent_mode: useAgentMode,
          domain: domain,
        }),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Analysis failed')
      }
      
      const result = await response.json()
      setAnalysisResult(result.analysis)
      setChartsCache(result.charts || [])
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleGenerateCharts = async () => {
    if (!currentDataset) return
    
    setIsGeneratingCharts(true)
    setShowVisuals(true)
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/analysis/generate-charts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_hash: currentDataset.hash,
        }),
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Chart generation failed')
      }
      
      const result = await response.json()
      // Store charts in cache for the Charts tab
      setChartsCache(result.charts || [])
    } catch (error) {
      console.error('Chart generation failed:', error)
    } finally {
      setIsGeneratingCharts(false)
    }
  }

  // No dataset loaded - show welcome screen like app.py
  if (!currentDataset) {
    return (
      <div className="h-full overflow-auto">
        <HeroHeader />
        
        {/* Feature Grid */}
        <div className="max-w-5xl mx-auto px-6 pb-8">
          <div className="grid grid-cols-3 gap-4 mb-10">
            {FEATURES.map(({ icon, title, desc }) => (
              <div key={title} className="feat-card">
                <div className="text-3xl mb-3">{icon}</div>
                <h3 className="font-semibold text-text-primary mb-1">{title}</h3>
                <p className="text-sm text-text-muted">{desc}</p>
              </div>
            ))}
          </div>
          
          {/* Upload Section - Centered */}
          <div className="max-w-xl mx-auto">
            <FileUploader 
              onUpload={handleFileUpload} 
              isLoading={isUploading} 
            />
            
            {uploadError && (
              <div className="mt-4 p-3 bg-accent-red/10 border border-accent-red/30 rounded-lg text-accent-red text-sm">
                ❌ {uploadError}
              </div>
            )}
          </div>
        </div>
      </div>
    )
  }

  // Dataset loaded - show analysis interface
  return (
    <div className="h-full overflow-auto">
      {/* Dataset Metrics Banner */}
      <div className="bg-bg-surface border-b border-border-subtle p-4">
        <div className="flex items-center justify-between max-w-7xl mx-auto">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <Database className="w-5 h-5 text-accent-blue" />
              <span className="font-medium">{currentDataset.filename}</span>
            </div>
            
            <div className="flex gap-4">
              <div className="text-center">
                <div className="text-xl font-bold">{currentDataset.rows.toLocaleString()}</div>
                <div className="text-xs text-text-muted uppercase">Rows</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold">{currentDataset.cols}</div>
                <div className="text-xs text-text-muted uppercase">Columns</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold">{currentDataset.numericCount}</div>
                <div className="text-xs text-text-muted uppercase">Numeric</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold">{currentDataset.categoricalCount}</div>
                <div className="text-xs text-text-muted uppercase">Categorical</div>
              </div>
              <div className="text-center">
                <div className="text-xl font-bold">{currentDataset.missingPct}%</div>
                <div className="text-xs text-text-muted uppercase">Missing</div>
              </div>
            </div>
          </div>
          
          <button
            onClick={() => setCurrentDataset(null)}
            className="btn-ghost text-sm"
          >
            📂 Change Dataset
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        {/* Analysis Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <BarChart3 className="w-7 h-7 text-accent-blue" />
            Comprehensive Analysis
          </h2>
          
          <div className="flex gap-3">
            {/* Generate Visuals Button */}
            {analysisResult && (
              <button
                onClick={() => {
                  if (showVisuals) {
                    setShowVisuals(false)
                  } else {
                    handleGenerateCharts()
                  }
                }}
                disabled={isGeneratingCharts}
                className="btn-secondary flex items-center gap-2"
              >
                {isGeneratingCharts ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Generating...
                  </>
                ) : showVisuals ? (
                  <>
                    <span>🔒</span>
                    Hide Charts
                  </>
                ) : (
                  <>
                    <span>📊</span>
                    Generate Visuals
                  </>
                )}
              </button>
            )}
            
            {/* Analyze Button */}
            {!analysisResult ? (
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="btn-primary flex items-center gap-2"
              >
                {isAnalyzing ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    {useAgentMode ? '🚀 Analyse with AI Agent' : '🚀 Analyse Data'}
                  </>
                )}
              </button>
            ) : (
              <button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="btn-secondary flex items-center gap-2"
              >
                <RefreshCw className="w-4 h-4" />
                Re-Analyse
              </button>
            )}
          </div>
        </div>

        {/* Preview Toggle */}
        <div className="mb-6">
          <button
            onClick={() => setShowPreview(!showPreview)}
            className="flex items-center gap-2 text-text-muted hover:text-text-primary transition-colors"
          >
            {showPreview ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            <span className="text-sm">{showPreview ? 'Hide' : 'Show'} Data Preview</span>
          </button>
          
          {showPreview && (
            <div className="mt-4">
              <DataPreview />
            </div>
          )}
        </div>

        {/* Analysis Results */}
        {analysisResult && (
          <div className="mt-6">
            <AnalysisResults />
          </div>
        )}
      </div>
    </div>
  )
}
