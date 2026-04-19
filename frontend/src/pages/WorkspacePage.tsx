import { useState } from 'react'
import { AppShell } from '../components/layout/AppShell'
import { ChatPane } from '../components/analysis/ChatPane'
import { DashboardPane } from '../components/analysis/DashboardPane'
import { FileManagerPanel } from '../components/filemanager/FileManagerPanel'

export default function WorkspacePage() {
  const [showFileManager, setShowFileManager] = useState(false)

  return (
    <AppShell onOpenFileManager={() => setShowFileManager(true)}>
      <div className="h-full flex">
        {/* Chat Pane - 42% */}
        <div className="w-[42%] border-r border-border-subtle">
          <ChatPane />
        </div>

        {/* Dashboard Pane - 58% */}
        <div className="w-[58%]">
          <DashboardPane />
        </div>
      </div>

      {/* File Manager Modal */}
      {showFileManager && (
        <FileManagerPanel onClose={() => setShowFileManager(false)} />
      )}
    </AppShell>
  )
}
