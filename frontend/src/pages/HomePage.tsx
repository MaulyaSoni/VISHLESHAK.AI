import { useState, useEffect } from 'react'
import { useAppStore } from '../store/useAppStore'
import { 
  Database, 
  MessageSquare, 
  TrendingUp, 
  Clock, 
  ArrowRight,
  Sparkles,
  BarChart3,
  Brain
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface RecentAnalysis {
  id: string
  title: string
  date: Date
  status: 'completed' | 'running' | 'failed'
}

export function HomePage() {
  const { user } = useAppStore()
  const navigate = useNavigate()
  const [recentAnalyses, setRecentAnalyses] = useState<RecentAnalysis[]>([])

  useEffect(() => {
    // Load recent analyses from API
    setRecentAnalyses([
      { id: '1', title: 'Sales Data Analysis', date: new Date(Date.now() - 3600000), status: 'completed' },
      { id: '2', title: 'Customer Churn Prediction', date: new Date(Date.now() - 86400000), status: 'completed' },
      { id: '3', title: 'Market Trend Analysis', date: new Date(Date.now() - 172800000), status: 'completed' }
    ])
  }, [])

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Good morning'
    if (hour < 18) return 'Good afternoon'
    return 'Good evening'
  }

  const quickActions = [
    {
      title: 'Data Agent',
      description: 'Automated data analysis with AI',
      icon: Database,
      color: 'accent-blue',
      action: () => navigate('/workspace?mode=DataAgent')
    },
    {
      title: 'Chat Assistant',
      description: 'Ask questions about your data',
      icon: MessageSquare,
      color: 'accent-cyan',
      action: () => navigate('/chat')
    },
    {
      title: 'Analysis',
      description: 'Manual data exploration',
      icon: TrendingUp,
      color: 'accent-green',
      action: () => navigate('/workspace?mode=Analysis')
    },
    {
      title: 'Kaggle Browser',
      description: 'Search and download datasets',
      icon: BarChart3,
      color: 'accent-blue',
      action: () => navigate('/kaggle')
    }
  ]

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Greeting Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">
          {getGreeting()}, {user?.name || 'User'}! 👋
        </h1>
        <p className="text-text-muted">
          Ready to analyze your data today?
        </p>
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-accent-cyan" />
          Quick Actions
        </h2>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map((action, index) => {
            const Icon = action.icon
            return (
              <button
                key={index}
                onClick={action.action}
                className="card-hover p-6 text-left group"
              >
                <div className={`w-12 h-12 rounded-xl bg-${action.color}/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                  <Icon className={`w-6 h-6 text-${action.color}`} />
                </div>
                
                <h3 className="text-base font-semibold text-text-primary mb-1">
                  {action.title}
                </h3>
                <p className="text-sm text-text-muted">
                  {action.description}
                </p>

                <div className="mt-4 flex items-center gap-2 text-sm text-accent-blue opacity-0 group-hover:opacity-100 transition-opacity">
                  <span>Get started</span>
                  <ArrowRight className="w-4 h-4" />
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Recent Analyses */}
      <div>
        <h2 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
          <Clock className="w-5 h-5 text-accent-blue" />
          Recent Analyses
        </h2>

        {recentAnalyses.length === 0 ? (
          <div className="card p-8 text-center">
            <Database className="w-12 h-12 text-text-muted mx-auto mb-3" />
            <h3 className="text-base font-semibold text-text-primary mb-1">
              No analyses yet
            </h3>
            <p className="text-sm text-text-muted">
              Start your first analysis to see it here
            </p>
          </div>
        ) : (
          <div className="grid gap-3">
            {recentAnalyses.map((analysis) => (
              <div
                key={analysis.id}
                className="card p-4 hover:border-accent-blue/50 transition-all cursor-pointer"
                onClick={() => navigate(`/workspace?analysis=${analysis.id}`)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <BarChart3 className="w-5 h-5 text-accent-blue" />
                    <div>
                      <h3 className="text-sm font-semibold text-text-primary">
                        {analysis.title}
                      </h3>
                      <p className="text-xs text-text-muted">
                        {analysis.date.toLocaleDateString()} at{' '}
                        {analysis.date.toLocaleTimeString([], { 
                          hour: '2-digit', 
                          minute: '2-digit' 
                        })}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-semibold ${
                        analysis.status === 'completed'
                          ? 'bg-accent-green/10 text-accent-green'
                          : analysis.status === 'running'
                          ? 'bg-accent-cyan/10 text-accent-cyan'
                          : 'bg-accent-red/10 text-accent-red'
                      }`}
                    >
                      {analysis.status}
                    </span>
                    <ArrowRight className="w-4 h-4 text-text-muted" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tips Section */}
      <div className="mt-8 card p-6 bg-gradient-accent/5 border-accent-blue/20">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-accent-cyan/10 flex items-center justify-center flex-shrink-0">
            <Brain className="w-6 h-6 text-accent-cyan" />
          </div>
          
          <div>
            <h3 className="text-base font-semibold text-text-primary mb-2">
              Pro Tip
            </h3>
            <p className="text-sm text-text-muted">
              Use the Data Agent for fully automated analysis. Just upload your dataset and describe what you want to find - the AI will plan and execute the entire analysis pipeline automatically.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
