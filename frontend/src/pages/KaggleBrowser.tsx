import { useState } from 'react'
import { Database, Download, Search, ExternalLink, Loader2 } from 'lucide-react'
import { apiFetch } from '../api/client'

interface KaggleDataset {
  slug: string
  title: string
  description: string
  votes: number
  downloads: number
}

export function KaggleBrowser() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<KaggleDataset[]>([])
  const [isSearching, setIsSearching] = useState(false)
  const [isDownloading, setIsDownloading] = useState<string | null>(null)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setIsSearching(true)
    try {
      const response = await apiFetch('/api/kaggle/search', {
        method: 'POST',
        body: JSON.stringify({ query: query.trim() })
      })

      if (!response.ok) throw new Error('Search failed')

      const data = await response.json()
      setResults(data.datasets || [])
    } catch (error) {
      console.error('Search error:', error)
    } finally {
      setIsSearching(false)
    }
  }

  const handleDownload = async (slug: string) => {
    setIsDownloading(slug)
    try {
      const response = await apiFetch('/api/kaggle/download', {
        method: 'POST',
        body: JSON.stringify({ dataset_slug: slug })
      })

      if (!response.ok) throw new Error('Download failed')

      alert('Dataset downloaded successfully!')
    } catch (error) {
      console.error('Download error:', error)
      alert('Failed to download dataset')
    } finally {
      setIsDownloading(null)
    }
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary mb-2 flex items-center gap-3">
          <Database className="w-6 h-6 text-accent-blue" />
          Kaggle Dataset Browser
        </h1>
        <p className="text-text-muted">
          Search and download datasets directly from Kaggle
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search Kaggle datasets..."
              className="input w-full pl-12"
            />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="btn-primary flex items-center gap-2 disabled:opacity-50"
          >
            {isSearching ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Search className="w-5 h-5" />
            )}
            Search
          </button>
        </div>
      </form>

      {/* Results */}
      {results.length === 0 && !isSearching && (
        <div className="text-center py-12">
          <Database className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Search for datasets
          </h3>
          <p className="text-text-muted">
            Enter a search term to find Kaggle datasets
          </p>
        </div>
      )}

      <div className="grid gap-4">
        {results.map((dataset) => (
          <div
            key={dataset.slug}
            className="card p-5 hover:border-accent-blue/50 transition-all duration-200"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-semibold text-text-primary mb-1 truncate">
                  {dataset.title}
                </h3>
                <p className="text-sm text-text-muted mb-3 line-clamp-2">
                  {dataset.description}
                </p>

                <div className="flex items-center gap-4 text-xs text-text-muted">
                  <span>⭐ {dataset.votes} votes</span>
                  <span>⬇️ {dataset.downloads.toLocaleString()} downloads</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href={`https://kaggle.com/datasets/${dataset.slug}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary flex items-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  View
                </a>
                <button
                  onClick={() => handleDownload(dataset.slug)}
                  disabled={isDownloading === dataset.slug}
                  className="btn-primary flex items-center gap-2 disabled:opacity-50"
                >
                  {isDownloading === dataset.slug ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  Download
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
