import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '../../store/useAppStore'
import { HeroHeader } from '../layout/HeroHeader'
import { Send, Bot, User, Sparkles, Loader2 } from 'lucide-react'
import { API_BASE_URL } from '@/api/client'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  meta?: {
    quality_score?: number
    quality_grade?: string
    confidence?: number
    tools_used?: string[]
    is_agent?: boolean
  }
}

export function ChatbotMode() {
  const { currentDataset, currentSessionId, addChatSession } = useAppStore()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [streamingContent, setStreamingContent] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamingContent])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [input])

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: input.trim(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)
    setStreamingContent('')

    // Save session title from first message
    if (messages.length === 0) {
      addChatSession({
        id: currentSessionId,
        title: userMessage.content.slice(0, 45) + (userMessage.content.length > 45 ? '...' : ''),
        timestamp: Date.now(),
      })
    }

    try {
      // If we don't yet have a DB-backed conversation id, create one.
      // Sidebar will normally create it, but this makes Chat robust when user types immediately.
      let sessionId = currentSessionId
      if (!/^\d+$/.test(sessionId)) {
        try {
          const resp = await fetch(`${API_BASE_URL}/api/history/conversations`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('vishleshak_token')}`,
            },
            body: JSON.stringify({ title: userMessage.content.slice(0, 45) }),
          })
          if (resp.ok) {
            const created = await resp.json()
            sessionId = String(created.id)
          }
        } catch {
          // ignore
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
          dataset_hash: currentDataset?.hash,
        }),
      })

      if (!response.ok) throw new Error('Chat request failed')

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      let fullContent = ''

      if (reader) {
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          
          const chunk = decoder.decode(value, { stream: true })
          const lines = chunk.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                if (data.chunk) {
                  fullContent += data.chunk
                  setStreamingContent(fullContent)
                }
                if (data.done) {
                  const assistantMessage: Message = {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: fullContent || data.response || 'No response generated.',
                    meta: {
                      quality_score: data.quality_score,
                      quality_grade: data.quality_grade,
                      confidence: data.confidence,
                      tools_used: data.tools_used,
                      is_agent: data.is_agent,
                    },
                  }
                  setMessages(prev => [...prev, assistantMessage])
                  setStreamingContent('')
                }
              } catch (e) {
                // Ignore parse errors for incomplete chunks
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      const errorMessage: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: '❌ I encountered an error processing your question. Please try again.',
        meta: { quality_grade: 'F', quality_score: 0 },
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const getGradeColor = (grade?: string) => {
    switch (grade) {
      case 'A': return 'text-accent-green'
      case 'B': return 'text-accent-cyan'
      case 'C': return 'text-accent-yellow'
      case 'D': case 'F': return 'text-accent-red'
      default: return 'text-text-muted'
    }
  }

  return (
    <div className="h-full flex flex-col">
      {messages.length === 0 ? (
        // Welcome screen
        <div className="flex-1 overflow-auto">
          <HeroHeader />
          
          <div className="max-w-3xl mx-auto px-6 pb-8">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-2">💬 RAG Chatbot</h2>
              <p className="text-text-muted">
                Ask questions about your data. The AI uses Retrieval-Augmented Generation 
                to provide accurate, data-aware answers.
              </p>
              {!currentDataset && (
                <div className="mt-4 p-4 bg-accent-yellow/10 border border-accent-yellow/30 rounded-lg">
                  <p className="text-accent-yellow text-sm">
                    ⚠️ No dataset loaded. Upload a dataset in Analysis mode for data-aware responses.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : (
        // Chat messages
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`chat-msg ${message.role === 'user' ? 'chat-msg-user' : 'chat-msg-bot'}`}
              >
                {/* Message Header */}
                <div className="flex items-center gap-2 mb-2">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                    message.role === 'user' 
                      ? 'bg-accent-blue text-white' 
                      : 'bg-accent-green text-white'
                  }`}>
                    {message.role === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
                  </div>
                  <span className="text-sm font-medium text-text-muted">
                    {message.role === 'user' ? 'You' : 'Vishleshak AI'}
                  </span>
                  {message.meta?.quality_grade && (
                    <span className={`text-xs ml-auto ${getGradeColor(message.meta.quality_grade)}`}>
                      Grade: {message.meta.quality_grade} 
                      {message.meta.quality_score && `(${Math.round(message.meta.quality_score)}/100)`}
                    </span>
                  )}
                </div>
                
                {/* Message Content */}
                <div className="prose prose-invert max-w-none">
                  <p className="whitespace-pre-wrap text-text-primary leading-relaxed">
                    {message.content}
                  </p>
                </div>

                {/* Meta info */}
                {message.meta?.tools_used && message.meta.tools_used.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1">
                    {message.meta.tools_used.map((tool) => (
                      <span key={tool} className="badge text-xs">
                        🔧 {tool}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
            
            {/* Streaming message */}
            {streamingContent && (
              <div className="chat-msg chat-msg-bot">
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-full bg-accent-green text-white flex items-center justify-center text-xs">
                    <Bot className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-sm font-medium text-text-muted">Vishleshak AI</span>
                  <span className="text-xs text-accent-cyan animate-pulse ml-auto">typing...</span>
                </div>
                <p className="whitespace-pre-wrap text-text-primary leading-relaxed">
                  {streamingContent}
                </p>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="border-t border-border-subtle bg-bg-surface p-4">
        <div className="max-w-3xl mx-auto">
          <div className="relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={currentDataset 
                ? "Ask a question about your data..." 
                : "Ask a general question or upload data first..."
              }
              className="textarea w-full pr-12 min-h-[60px] max-h-[200px]"
              rows={1}
              disabled={isLoading}
            />
            <button
              onClick={handleSubmit}
              disabled={!input.trim() || isLoading}
              className="absolute right-3 bottom-3 p-2 bg-accent-blue text-white rounded-lg 
                         hover:bg-accent-blue/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
          <p className="text-xs text-text-muted mt-2 text-center">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
      </div>
    </div>
  )
}
