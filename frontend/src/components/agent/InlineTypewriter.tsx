import { useState, useEffect, useRef } from 'react'
import { cn } from '../../utils/cn'

interface InlineTypewriterProps {
  text: string
  speed?: number
  onComplete?: () => void
  className?: string
  cursorChar?: string
  startOnMount?: boolean
}

export function InlineTypewriter({
  text,
  speed = 20,
  onComplete,
  className,
  cursorChar = '▊',
  startOnMount = true
}: InlineTypewriterProps) {
  const [displayedText, setDisplayedText] = useState('')
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    if (!startOnMount) return
    
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
    }

    // Reset state when text changes
    setDisplayedText('')
    setCurrentIndex(0)
    setIsComplete(false)

    intervalRef.current = setInterval(() => {
      setCurrentIndex((prev) => {
        if (prev >= text.length) {
          setIsComplete(true)
          if (intervalRef.current) {
            clearInterval(intervalRef.current)
          }
          onComplete?.()
          return prev
        }
        
        setDisplayedText(text.slice(0, prev + 1))
        return prev + 1
      })
    }, speed)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [text, speed, onComplete, startOnMount])

  return (
    <span className={cn('font-mono text-sm', className)}>
      {displayedText}
      {!isComplete && (
        <span className="text-accent-cyan animate-pulse">{cursorChar}</span>
      )}
    </span>
  )
}
