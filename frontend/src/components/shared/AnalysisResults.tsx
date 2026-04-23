import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { 
  FileText, 
  BarChart3, 
  Brain, 
  Code, 
  AlertCircle,
  CheckCircle,
  TrendingUp,
  Lightbulb,
  Download
} from 'lucide-react'
import Plot from 'react-plotly.js'

const TABS = [
  { key: 'summary', label: 'Summary', icon: FileText },
  { key: 'charts', label: 'Charts', icon: BarChart3 },
  { key: 'insights', label: 'AI Insights', icon: Brain },
  { key: 'stats', label: 'Statistics', icon: TrendingUp },
  { key: 'raw', label: 'Raw JSON', icon: Code },
]

interface AnalysisResult {
  executive_summary?: string
  profile?: {
    rows: number
    columns: number
    numeric_count: number
    categorical_count: number
  }
  statistics?: Record<string, unknown>
  ai_insights?: string
  key_findings?: string[]
  recommendations?: string[]
  anomalies_or_risks?: string[]
  is_v2?: boolean
}

export function AnalysisResults() {
  const { analysisResult, chartsCache } = useAppStore()
  const [activeTab, setActiveTab] = useState('summary')

  if (!analysisResult) {
    return (
      <div className="card p-8 text-center">
        <BarChart3 className="w-16 h-16 mx-auto mb-4 text-text-muted opacity-50" />
        <p className="text-text-muted text-lg">No analysis results yet.</p>
        <p className="text-text-muted text-sm mt-2">
          Upload a dataset and click "Analyse Data" to get started.
        </p>
      </div>
    )
  }

  const result = analysisResult as AnalysisResult

  return (
    <div className="space-y-4">
      {/* Result Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <CheckCircle className="w-6 h-6 text-accent-green" />
          <h3 className="text-xl font-semibold">
            Analysis Complete {result.is_v2 && <span className="badge-accent text-xs ml-2">v2</span>}
          </h3>
        </div>
        <button className="btn-secondary flex items-center gap-2">
          <Download className="w-4 h-4" />
          Export Report
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border-subtle">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={`tab flex items-center gap-2 ${activeTab === key ? 'active' : ''}`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'summary' && (
          <div className="space-y-4">
            {/* Profile Metrics */}
            {result.profile && (
              <div className="grid grid-cols-4 gap-3">
                <div className="metric-card">
                  <div className="metric-value">{result.profile.rows?.toLocaleString()}</div>
                  <div className="metric-label">Rows</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{result.profile.columns}</div>
                  <div className="metric-label">Columns</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{result.profile.numeric_count}</div>
                  <div className="metric-label">Numeric</div>
                </div>
                <div className="metric-card">
                  <div className="metric-value">{result.profile.categorical_count}</div>
                  <div className="metric-label">Categorical</div>
                </div>
              </div>
            )}

            {/* Executive Summary */}
            {result.executive_summary && (
              <div className="card p-5">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-accent-blue" />
                  Executive Summary
                </h4>
                <p className="text-text-primary leading-relaxed">{result.executive_summary}</p>
              </div>
            )}

            {/* Key Findings & Recommendations */}
            <div className="grid grid-cols-2 gap-4">
              {result.key_findings && result.key_findings.length > 0 && (
                <div className="card p-5">
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-accent-cyan" />
                    Key Findings
                  </h4>
                  <ul className="space-y-2">
                    {result.key_findings.map((finding, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-text-primary">
                        <span className="text-accent-green mt-1">✓</span>
                        <span>{finding}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.recommendations && result.recommendations.length > 0 && (
                <div className="card p-5">
                  <h4 className="font-semibold mb-3 flex items-center gap-2">
                    <Lightbulb className="w-5 h-5 text-accent-yellow" />
                    Recommendations
                  </h4>
                  <ul className="space-y-2">
                    {result.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-text-primary">
                        <span className="text-accent-blue mt-1">→</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Anomalies */}
            {result.anomalies_or_risks && result.anomalies_or_risks.length > 0 && (
              <div className="card p-5 border-accent-red/30">
                <h4 className="font-semibold mb-3 flex items-center gap-2 text-accent-red">
                  <AlertCircle className="w-5 h-5" />
                  Anomalies & Risks
                </h4>
                <ul className="space-y-2">
                  {result.anomalies_or_risks.map((anomaly, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-text-primary">
                      <span className="text-accent-red mt-1">⚠</span>
                      <span>{anomaly}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {activeTab === 'charts' && (
          <div className="space-y-4">
            {chartsCache && chartsCache.length > 0 ? (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {chartsCache.map((chart: any, idx) => (
                  <div key={idx} className="card p-4">
                    <h4 className="font-medium mb-3">{chart.title || `Chart ${idx + 1}`}</h4>
                    {chart.plotly_json ? (
                      <Plot
                        data={chart.plotly_json.data}
                        layout={{
                          ...chart.plotly_json.layout,
                          autosize: true,
                          height: 400,
                          margin: { l: 50, r: 30, t: 50, b: 50 }
                        }}
                        config={{
                          responsive: true,
                          displayModeBar: true,
                          modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                          displaylogo: false
                        }}
                        className="w-full"
                        useResizeHandler={true}
                        style={{ width: '100%' }}
                      />
                    ) : chart.component || (
                      <div className="h-64 bg-bg-elevated rounded-lg flex items-center justify-center text-text-muted">
                        Chart visualization
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="card p-8 text-center text-text-muted">
                <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>No charts generated for this analysis.</p>
                <p className="text-sm mt-2">Click "Generate Visuals" to create interactive charts.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="card p-5">
            <h4 className="font-semibold mb-3 flex items-center gap-2">
              <Brain className="w-5 h-5 text-accent-blue" />
              AI-Generated Insights
            </h4>
            {result.ai_insights ? (
              <div className="prose prose-invert max-w-none">
                <p className="text-text-primary leading-relaxed whitespace-pre-wrap">
                  {result.ai_insights}
                </p>
              </div>
            ) : (
              <p className="text-text-muted">No AI insights available.</p>
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="card p-5">
            <h4 className="font-semibold mb-3">Statistical Analysis</h4>
            {result.statistics ? (
              <pre className="bg-bg-elevated p-4 rounded-lg overflow-auto text-sm">
                {JSON.stringify(result.statistics, null, 2)}
              </pre>
            ) : (
              <p className="text-text-muted">No detailed statistics available.</p>
            )}
          </div>
        )}

        {activeTab === 'raw' && (
          <div className="card p-5">
            <h4 className="font-semibold mb-3">Raw JSON Output</h4>
            <pre className="bg-bg-elevated p-4 rounded-lg overflow-auto text-xs max-h-[600px]">
              {JSON.stringify(analysisResult, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
