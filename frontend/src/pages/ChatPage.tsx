import { useState, useEffect, useRef } from 'react'
import { ChatMessage } from '../components/analysis/ChatMessage'
import { QualityBadge, QualityGrade } from '../components/analysis/QualityBadge'
import { ReasoningTrace, ReasoningStep } from '../components/analysis/ReasoningTrace'
import { ConversationHistory, Conversation } from '../components/analysis/ConversationHistory'
import { Send, Loader2, Sparkles, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { apiFetch } from '../api/client'

interface ChatMessageData {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  quality?: QualityGrade
  confidence?: number
  reasoning?: ReasoningStep[]
}

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageData[]>([])
  const [input, setInput] = useState('')
  const [isSending, setIsSending] = useState(false)
  const [showSidebar, setShowSidebar] = useState(true)
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      title: 'Data Analysis Help',
      messageCount: 12,
      lastMessage: new Date(Date.now() - 1000 * 60 * 30),
      isActive: true
    },
    {
      id: '2',
      title: 'ML Model Questions',
      messageCount: 8,
      lastMessage: new Date(Date.now() - 1000 * 60 * 60 * 2),
      isActive: false
    }
  ])
  
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isSending) return

    const userMessage: ChatMessageData = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsSending(true)

    try {
      // Call backend chat API
      const response = await apiFetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversations.find(c => c.isActive)?.id
        })
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()

      const assistantMessage: ChatMessageData = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        quality: data.quality_grade || 'B',
        confidence: data.confidence || 0.85,
        reasoning: data.reasoning_trace || []
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (error) {
      const errorMessage: ChatMessageData = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsSending(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="h-screen flex bg-bg-base">
      {/* Conversation Sidebar */}
      {showSidebar && (
        <div className="w-80 border-r border-border-subtle bg-bg-surface flex flex-col">
          <div className="p-4 border-b border-border-subtle">
            <h2 className="text-sm font-semibold text-text-primary">
              Conversations
            </h2>
          </div>

          <div className="flex-1 overflow-y-auto">
            <ConversationHistory
              conversations={conversations}
              onSelect={(id) => {
                setConversations((prev) =>
                  prev.map((c) => ({
                    ...c,
                    isActive: c.id === id
                  }))
                )
              }}
              className="p-2"
            />
          </div>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border-subtle bg-bg-surface">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="p-2 rounded-lg hover:bg-bg-elevated transition-colors"
            >
              {showSidebar ? (
                <PanelLeftClose className="w-5 h-5 text-text-muted" />
              ) : (
                <PanelLeftOpen className="w-5 h-5 text-text-muted" />
              )}
            </button>

            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-accent-cyan" />
              <h1 className="text-lg font-semibold text-text-primary">
                AI Chat Assistant
              </h1>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-accent-cyan/10 mb-4">
                <Sparkles className="w-8 h-8 text-accent-cyan" />
              </div>
              <h3 className="text-xl font-semibold text-text-primary mb-2">
                How can I help you today?
              </h3>
              <p className="text-text-muted max-w-md">
                Ask me about data analysis, machine learning, or get help with your datasets.
              </p>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div key={msg.id}>
                  <ChatMessage
                    role={msg.role}
                    content={msg.content}
                    timestamp={msg.timestamp}
                  />

                  {/* Show quality badge and reasoning for assistant messages */}
                  {msg.role === 'assistant' && msg.quality && (
                    <div className="ml-11 mb-4 space-y-2">
                      <QualityBadge
                        grade={msg.quality}
                        confidence={msg.confidence}
                      />

                      {msg.reasoning && msg.reasoning.length > 0 && (
                        <ReasoningTrace steps={msg.reasoning} />
                      )}
                    </div>
                  )}
                </div>
              ))}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-border-subtle p-4 bg-bg-surface">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message..."
              className="textarea flex-1 resize-none"
              rows={2}
              disabled={isSending}
            />

            <button
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              className="btn-primary self-end flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isSending ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
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
