import { useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import { cn } from '../../utils/cn'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

interface ToastProps {
  toast: Toast
  onRemove: (id: string) => void
}

const toastConfig = {
  success: {
    icon: CheckCircle,
    color: 'bg-accent-green/10 border-accent-green/30 text-accent-green',
    iconColor: 'text-accent-green'
  },
  error: {
    icon: AlertCircle,
    color: 'bg-accent-red/10 border-accent-red/30 text-accent-red',
    iconColor: 'text-accent-red'
  },
  warning: {
    icon: AlertTriangle,
    color: 'bg-yellow-500/10 border-yellow-500/30 text-yellow-500',
    iconColor: 'text-yellow-500'
  },
  info: {
    icon: Info,
    color: 'bg-accent-blue/10 border-accent-blue/30 text-accent-blue',
    iconColor: 'text-accent-blue'
  }
}

function ToastItem({ toast, onRemove }: ToastProps) {
  const [isVisible, setIsVisible] = useState(true)
  const config = toastConfig[toast.type]
  const Icon = config.icon

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false)
      setTimeout(() => onRemove(toast.id), 300)
    }, toast.duration || 4000)

    return () => clearTimeout(timer)
  }, [toast.id, toast.duration, onRemove])

  return (
    <div
      className={cn(
        'flex items-center gap-3 px-4 py-3 rounded-lg border shadow-lg',
        'transform transition-all duration-300',
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0',
        config.color
      )}
    >
      <Icon className={cn('w-5 h-5 flex-shrink-0', config.iconColor)} />
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => {
          setIsVisible(false)
          setTimeout(() => onRemove(toast.id), 300)
        }}
        className="flex-shrink-0 hover:opacity-70 transition-opacity"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}

// Toast store
let toasts: Toast[] = []
let listeners: ((toasts: Toast[]) => void)[] = []

function notify(toast: Omit<Toast, 'id'>) {
  const id = Math.random().toString(36).substr(2, 9)
  const newToast = { ...toast, id }
  toasts = [...toasts, newToast]
  listeners.forEach(fn => fn(toasts))
  return id
}

export const toast = {
  success: (message: string, duration?: number) => 
    notify({ type: 'success', message, duration }),
  error: (message: string, duration?: number) => 
    notify({ type: 'error', message, duration }),
  warning: (message: string, duration?: number) => 
    notify({ type: 'warning', message, duration }),
  info: (message: string, duration?: number) => 
    notify({ type: 'info', message, duration })
}

function ToastContainer() {
  const [toastList, setToastList] = useState<Toast[]>([])

  useEffect(() => {
    const listener = (newToasts: Toast[]) => {
      setToastList([...newToasts])
    }
    listeners.push(listener)
    return () => {
      listeners = listeners.filter(l => l !== listener)
    }
  }, [])

  const removeToast = (id: string) => {
    toasts = toasts.filter(t => t.id !== id)
    listeners.forEach(fn => fn(toasts))
  }

  return (
    <div className="fixed bottom-4 right-4 z-50 space-y-2 max-w-sm">
      {toastList.map(t => (
        <ToastItem key={t.id} toast={t} onRemove={removeToast} />
      ))}
    </div>
  )
}

// Export function to render toast container
export function renderToastContainer() {
  const container = document.createElement('div')
  container.id = 'toast-root'
  document.body.appendChild(container)
  const root = createRoot(container)
  root.render(<ToastContainer />)
}
