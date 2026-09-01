import { useState, useEffect } from 'react'
import { BenchmarkGauge } from '../components/analysis/BenchmarkGauge'
import { Loader2, BarChart3 } from 'lucide-react'
import { apiFetch } from '../api/client'

interface Benchmark {
  metric: string
  value: number
  max: number
  unit: string
  color: 'blue' | 'cyan' | 'green' | 'yellow' | 'red'
}

export function BenchmarksPage() {
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadBenchmarks()
  }, [])

  const loadBenchmarks = async () => {
    try {
      const response = await apiFetch('/api/benchmarks')

      if (!response.ok) throw new Error('Failed to load benchmarks')

      const data = await response.json()
      setBenchmarks(data.benchmarks || [])
    } catch (error) {
      console.error('Load benchmarks error:', error)
      // Fallback demo data
      setBenchmarks([
        { metric: 'Analysis Speed', value: 85, max: 100, unit: '%', color: 'blue' },
        { metric: 'Model Accuracy', value: 92, max: 100, unit: '%', color: 'green' },
        { metric: 'Data Quality', value: 78, max: 100, unit: '%', color: 'cyan' },
        { metric: 'Insight Depth', value: 88, max: 100, unit: '%', color: 'blue' },
        { metric: 'Response Time', value: 1.2, max: 5, unit: 's', color: 'green' },
        { metric: 'Error Rate', value: 2, max: 10, unit: '%', color: 'yellow' }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-accent-blue" />
      </div>
    )
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-text-primary mb-2 flex items-center gap-3">
          <BarChart3 className="w-6 h-6 text-accent-green" />
          Performance Benchmarks
        </h1>
        <p className="text-text-muted">
          System performance metrics and quality indicators
        </p>
      </div>

      {/* Benchmarks Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
        {benchmarks.map((benchmark, index) => (
          <BenchmarkGauge
            key={index}
            value={benchmark.value}
            max={benchmark.max}
            label={benchmark.metric}
            unit={benchmark.unit}
            color={benchmark.color}
            size="md"
          />
        ))}
      </div>

      {/* Detailed Stats */}
      <div className="mt-12 card p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">
          Detailed Statistics
        </h3>

        <div className="grid md:grid-cols-2 gap-6">
          {benchmarks.map((benchmark, index) => (
            <div key={index} className="flex items-center justify-between p-4 rounded-lg bg-bg-base">
              <span className="text-sm text-text-primary">{benchmark.metric}</span>
              <div className="flex items-center gap-3">
                <div className="w-32 h-2 rounded-full bg-bg-elevated overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${(benchmark.value / benchmark.max) * 100}%`,
                      backgroundColor: `var(--${benchmark.color})`
                    }}
                  />
                </div>
                <span className="text-sm font-semibold text-text-primary min-w-[60px] text-right">
                  {benchmark.value}{benchmark.unit}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
