import { ReactNode } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

interface AppShellProps {
  children: ReactNode
  onOpenFileManager?: () => void
}

export function AppShell({ children, onOpenFileManager }: AppShellProps) {
  return (
    <div className="min-h-screen bg-bg-base flex">
      <Sidebar onOpenFileManager={onOpenFileManager} />
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar />
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
