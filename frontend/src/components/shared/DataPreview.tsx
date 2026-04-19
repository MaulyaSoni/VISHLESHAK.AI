import { useState, useEffect } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { Table, AlertCircle, Database } from 'lucide-react'
import { API_BASE_URL } from '@/api/client'

interface DataPreviewProps {
  datasetHash?: string
}

interface DatasetInfo {
  columns: string[]
  dtypes: Record<string, string>
  sample: Record<string, unknown>[]
  shape: [number, number]
  missing: Record<string, number>
}

export function DataPreview({ datasetHash }: DataPreviewProps) {
  const { currentDataset } = useAppStore()
  const [data, setData] = useState<DatasetInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      const hash = datasetHash || currentDataset?.hash
      if (!hash) return

      try {
        setLoading(true)
        const response = await fetch(`${API_BASE_URL}/api/datasets/${hash}/preview`)
        if (!response.ok) throw new Error('Failed to fetch preview')
        const result = await response.json()
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [datasetHash, currentDataset])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-accent-blue/30 border-t-accent-blue rounded-full animate-spin" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="card p-6 text-center">
        <AlertCircle className="w-12 h-12 text-accent-red mx-auto mb-3" />
        <p className="text-accent-red">{error}</p>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="card p-6 text-center text-text-muted">
        <Database className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No data available</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Dataset Metrics */}
      <div className="grid grid-cols-5 gap-3">
        <div className="metric-card">
          <div className="metric-value">{data.shape[0].toLocaleString()}</div>
          <div className="metric-label">Rows</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">{data.shape[1]}</div>
          <div className="metric-label">Columns</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">
            {Object.values(data.dtypes).filter(t => ['int64', 'float64'].includes(t)).length}
          </div>
          <div className="metric-label">Numeric</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">
            {Object.values(data.dtypes).filter(t => ['object', 'category'].includes(t)).length}
          </div>
          <div className="metric-label">Categorical</div>
        </div>
        <div className="metric-card">
          <div className="metric-value">
            {Object.values(data.missing).reduce((a, b) => a + b, 0) > 0 
              ? `${((Object.values(data.missing).reduce((a, b) => a + b, 0) / (data.shape[0] * data.shape[1])) * 100).toFixed(1)}%`
              : '0%'}
          </div>
          <div className="metric-label">Missing</div>
        </div>
      </div>

      {/* Data Table */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-border-subtle flex items-center gap-2">
          <Table className="w-5 h-5 text-accent-blue" />
          <h3 className="font-semibold">Data Preview (First 10 rows)</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-bg-elevated">
              <tr>
                {data.columns.map((col) => (
                  <th 
                    key={col}
                    className="px-4 py-3 text-left text-text-muted font-medium border-b border-border-subtle"
                  >
                    <div className="flex items-center gap-2">
                      <span className="truncate max-w-[150px]">{col}</span>
                      <span className="text-xs px-1.5 py-0.5 rounded bg-bg-surface text-text-muted">
                        {data.dtypes[col]}
                      </span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.sample.map((row, idx) => (
                <tr key={idx} className="border-b border-border-subtle/50 hover:bg-bg-elevated/50">
                  {data.columns.map((col) => (
                    <td key={col} className="px-4 py-2.5 text-text-primary">
                      <span className="truncate max-w-[200px] block">
                        {row[col] === null || row[col] === undefined 
                          ? <span className="text-text-muted/50">null</span>
                          : String(row[col]).slice(0, 50)}
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Column Info */}
      <div className="card p-4">
        <h4 className="font-semibold mb-3">Column Information</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {data.columns.map((col) => (
            <div 
              key={col}
              className="flex items-center justify-between px-3 py-2 rounded-lg bg-bg-elevated"
            >
              <span className="text-sm truncate max-w-[120px]">{col}</span>
              <span className="text-xs text-text-muted">{data.dtypes[col]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
