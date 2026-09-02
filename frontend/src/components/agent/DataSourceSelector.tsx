import { useState } from 'react'
import { cn } from '../../utils/cn'
import { Upload, Link, Database, FileText } from 'lucide-react'

export type DataSourceType = 'upload' | 'url' | 'kaggle'

interface DataSourceSelectorProps {
  onSourceSelected: (type: DataSourceType, data: any) => void
  className?: string
}

export function DataSourceSelector({ onSourceSelected, className }: DataSourceSelectorProps) {
  const [activeTab, setActiveTab] = useState<DataSourceType>('upload')
  const [url, setUrl] = useState('')
  const [kaggleQuery, setKaggleQuery] = useState('')

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      onSourceSelected('upload', { file })
    }
  }

  const handleUrlSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      onSourceSelected('url', { url: url.trim() })
      setUrl('')
    }
  }

  const handleKaggleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (kaggleQuery.trim()) {
      onSourceSelected('kaggle', { query: kaggleQuery.trim() })
      setKaggleQuery('')
    }
  }

  const tabs = [
    { id: 'upload' as const, label: 'Upload', icon: Upload },
    { id: 'url' as const, label: 'URL', icon: Link },
    { id: 'kaggle' as const, label: 'Kaggle', icon: Database },
  ]

  return (
    <div className={cn('card p-4', className)}>
      <h3 className="text-sm font-semibold text-text-primary mb-3 flex items-center gap-2">
        <FileText className="w-4 h-4 text-accent-blue" />
        Data Source
      </h3>

      {/* Tabs */}
      <div className="flex gap-1 mb-4 p-1 bg-bg-base rounded-lg">
        {tabs.map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex-1 flex items-center justify-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-accent-blue text-white'
                  : 'text-text-muted hover:text-text-primary hover:bg-bg-elevated'
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[120px]">
        {activeTab === 'upload' && (
          <div className="upload-zone">
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileUpload}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="w-8 h-8 text-text-muted mx-auto mb-2" />
              <p className="text-sm text-text-primary mb-1">
                Click to upload or drag and drop
              </p>
              <p className="text-xs text-text-muted">
                CSV, Excel files supported
              </p>
            </label>
          </div>
        )}

        {activeTab === 'url' && (
          <form onSubmit={handleUrlSubmit} className="space-y-3">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/data.csv"
              className="input w-full text-sm"
              required
            />
            <button type="submit" className="btn-primary w-full text-sm">
              Load from URL
            </button>
          </form>
        )}

        {activeTab === 'kaggle' && (
          <form onSubmit={handleKaggleSearch} className="space-y-3">
            <input
              type="text"
              value={kaggleQuery}
              onChange={(e) => setKaggleQuery(e.target.value)}
              placeholder="Search Kaggle datasets..."
              className="input w-full text-sm"
              required
            />
            <button type="submit" className="btn-primary w-full text-sm">
              Search Kaggle
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
