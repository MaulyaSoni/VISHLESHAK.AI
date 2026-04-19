import { useState } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { useAgentStore } from '../../store/useAgentStore'
import { BarChart3, PieChart, Activity, FileText } from 'lucide-react'

export function DashboardPane() {
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'stats'>('overview')
  const { currentDataset } = useAppStore()
  const { status, charts, insights } = useAgentStore()

  if (!currentDataset) {
    return (
      <div className="h-full flex items-center justify-center text-text-muted">
        <div className="text-center">
          <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Load a dataset to see analysis dashboard</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      {/* Tabs */}
      <div className="flex border-b border-border-subtle">
        {[
          { key: 'overview', label: 'Overview', icon: Activity },
          { key: 'charts', label: 'Charts', icon: PieChart },
          { key: 'stats', label: 'Stats', icon: BarChart3 },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'text-accent-blue border-b-2 border-accent-blue'
                : 'text-text-muted hover:text-text-primary'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Dataset Info */}
            <div className="grid grid-cols-4 gap-4">
              <div className="card p-4">
                <p className="text-sm text-text-muted">Rows</p>
                <p className="text-2xl font-semibold text-text-primary">
                  {currentDataset.rows.toLocaleString()}
                </p>
              </div>
              <div className="card p-4">
                <p className="text-sm text-text-muted">Columns</p>
                <p className="text-2xl font-semibold text-text-primary">
                  {currentDataset.cols}
                </p>
              </div>
              <div className="card p-4">
                <p className="text-sm text-text-muted">Charts</p>
                <p className="text-2xl font-semibold text-text-primary">
                  {charts.length}
                </p>
              </div>
              <div className="card p-4">
                <p className="text-sm text-text-muted">Status</p>
                <p className={`text-2xl font-semibold capitalize ${
                  status === 'running' ? 'text-accent-blue' :
                  status === 'done' ? 'text-accent-green' :
                  status === 'error' ? 'text-accent-red' :
                  'text-text-muted'
                }`}>
                  {status}
                </p>
              </div>
            </div>

            {/* Insights */}
            {insights && (
              <div className="card p-4">
                <h3 className="text-lg font-medium mb-3">Insights</h3>
                <p className="text-text-primary whitespace-pre-wrap">{insights}</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'charts' && (
          <div className="space-y-4">
            {charts.length === 0 ? (
              <div className="text-center text-text-muted py-20">
                <PieChart className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No charts generated yet</p>
              </div>
            ) : (
              charts.map((chart) => (
                <div key={chart.id} className="card p-4">
                  <h4 className="font-medium mb-2">{chart.caption}</h4>
                  <p className="text-sm text-text-muted">{chart.type}</p>
                  <p className="text-xs text-text-muted mt-1">{chart.path}</p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'stats' && (
          <div className="text-center text-text-muted py-20">
            <BarChart3 className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Statistical analysis will appear here</p>
          </div>
        )}
      </div>
    </div>
  )
}
