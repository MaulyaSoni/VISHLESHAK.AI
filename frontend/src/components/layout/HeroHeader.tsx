import { Microscope, Brain, Link2, Lightbulb, BarChart3, Wrench, Bot } from 'lucide-react'

const BADGES = [
  { icon: Brain, label: 'Memory' },
  { icon: Link2, label: 'RAG' },
  { icon: Lightbulb, label: 'Chain-of-Thought' },
  { icon: BarChart3, label: 'Quality Scoring' },
  { icon: Wrench, label: 'Agentic Tools' },
  { icon: Bot, label: 'ReAct Agent' },
]

export function HeroHeader() {
  return (
    <div className="text-center py-8 px-4">
      {/* Logo */}
      <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-accent-blue via-accent-cyan to-accent-green flex items-center justify-center text-white text-4xl shadow-glow animate-float">
        <Microscope className="w-12 h-12" />
      </div>
      
      {/* Title */}
      <h1 className="text-4xl font-bold mb-3 hero-gradient">
        Vishleshak AI
      </h1>
      
      {/* Subtitle */}
      <p className="text-text-muted text-lg mb-6 max-w-2xl mx-auto">
        The Analyser of Your Financial Data — Powered by Next-Level RAG Intelligence
      </p>
      
      {/* Badges */}
      <div className="flex flex-wrap justify-center gap-2">
        {BADGES.map(({ icon: Icon, label }) => (
          <span 
            key={label}
            className="badge-accent flex items-center gap-1.5 px-3 py-1.5"
          >
            <Icon className="w-3.5 h-3.5" />
            {label}
          </span>
        ))}
      </div>
      
      {/* Divider */}
      <div className="mt-8 border-b border-border-subtle" />
    </div>
  )
}
