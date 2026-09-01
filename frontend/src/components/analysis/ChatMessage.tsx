import { cn } from '../../utils/cn'
import ReactMarkdown from 'react-markdown'
import { User, Bot } from 'lucide-react'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  timestamp?: Date
  className?: string
}

export function ChatMessage({ role, content, timestamp, className }: ChatMessageProps) {
  const isUser = role === 'user'

  return (
    <div
      className={cn(
        'flex gap-3 mb-4',
        isUser ? 'flex-row-reverse' : 'flex-row',
        className
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser ? 'bg-accent-blue/10' : 'bg-accent-green/10'
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-accent-blue" />
        ) : (
          <Bot className="w-4 h-4 text-accent-green" />
        )}
      </div>

      {/* Message Bubble */}
      <div
        className={cn(
          'max-w-[75%] rounded-xl p-4',
          isUser
            ? 'bg-msg-user border-l-2 border-msg-user-border'
            : 'bg-msg-bot border-l-2 border-msg-bot-border'
        )}
      >
        <div className={cn('text-sm', isUser ? 'text-text-primary' : 'text-text-primary')}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <ReactMarkdown
              className="prose prose-sm max-w-none prose-invert"
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                code: ({ children }) => (
                  <code className="bg-bg-base px-1.5 py-0.5 rounded text-xs font-mono">
                    {children}
                  </code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-bg-base p-3 rounded-lg overflow-x-auto text-xs font-mono my-2">
                    {children}
                  </pre>
                ),
                ul: ({ children }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
                li: ({ children }) => <li className="mb-1">{children}</li>,
                h1: ({ children }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-bold mb-2">{children}</h3>,
              }}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>

        {/* Timestamp */}
        {timestamp && (
          <p className="text-xs text-text-muted mt-2">
            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </div>
  )
}
