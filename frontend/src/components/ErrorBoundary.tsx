import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo)
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-bg-base flex items-center justify-center">
          <div className="card p-8 max-w-md">
            <h2 className="text-xl font-semibold text-accent-red mb-4">Something went wrong</h2>
            <pre className="text-sm text-text-muted whitespace-pre-wrap">
              {this.state.error?.message}
            </pre>
            <button 
              onClick={() => window.location.reload()} 
              className="btn-primary mt-4"
            >
              Reload App
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
