import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useUploadFile, useScanFolder, useLoadPath } from '../../api/files'
import { useAppStore } from '../../store/useAppStore'
import { X, Upload, Folder, File, Loader2 } from 'lucide-react'

interface FileManagerPanelProps {
  onClose: () => void
}

export function FileManagerPanel({ onClose }: FileManagerPanelProps) {
  const [activeTab, setActiveTab] = useState<'upload' | 'path' | 'folder'>('upload')
  const [filePath, setFilePath] = useState('')
  const [folderPath, setFolderPath] = useState('')
  const [scannedFiles, setScannedFiles] = useState<any[]>([])
  
  const { addDataset, setCurrentDataset } = useAppStore()
  const uploadFile = useUploadFile()
  const scanFolder = useScanFolder()
  const loadPath = useLoadPath()

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    
    const file = acceptedFiles[0]
    try {
      const result = await uploadFile.mutateAsync(file)
      const dataset = {
        hash: result.dataset_hash,
        filename: result.filename,
        rows: result.rows,
        cols: result.cols,
        meta: result.meta,
      }
      addDataset(dataset)
      setCurrentDataset(dataset)
      onClose()
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }, [uploadFile, addDataset, setCurrentDataset, onClose])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/json': ['.json'],
    },
    maxFiles: 1,
  })

  const handleScanFolder = async () => {
    if (!folderPath) return
    try {
      const result = await scanFolder.mutateAsync(folderPath)
      setScannedFiles(result.files || [])
    } catch (error) {
      console.error('Scan failed:', error)
    }
  }

  const handleLoadPath = async () => {
    if (!filePath) return
    try {
      const result = await loadPath.mutateAsync(filePath)
      const dataset = {
        hash: result.dataset_hash,
        filename: result.filename,
        rows: result.rows,
        cols: result.cols,
        meta: result.meta,
      }
      addDataset(dataset)
      setCurrentDataset(dataset)
      onClose()
    } catch (error) {
      console.error('Load failed:', error)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-bg-surface rounded-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border-subtle">
          <h2 className="text-lg font-semibold">Load Dataset</h2>
          <button onClick={onClose} className="p-2 hover:bg-bg-elevated rounded-lg">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-border-subtle">
          {[
            { key: 'upload', label: 'Upload', icon: Upload },
            { key: 'path', label: 'File Path', icon: File },
            { key: 'folder', label: 'Folder', icon: Folder },
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'text-accent-blue border-b-2 border-accent-blue'
                  : 'text-text-muted hover:text-text-primary'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'upload' && (
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-12 text-center transition-colors ${
                isDragActive
                  ? 'border-accent-blue bg-accent-blue/10'
                  : 'border-border-subtle hover:border-text-muted'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 mx-auto mb-4 text-text-muted" />
              <p className="text-text-primary mb-2">
                {isDragActive ? 'Drop the file here' : 'Drag & drop a file here'}
              </p>
              <p className="text-sm text-text-muted">
                or click to select (CSV, XLSX, XLS, JSON)
              </p>
              {uploadFile.isPending && (
                <div className="mt-4 flex items-center justify-center gap-2 text-accent-blue">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Uploading...</span>
                </div>
              )}
            </div>
          )}

          {activeTab === 'path' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-text-muted mb-2">File Path</label>
                <input
                  type="text"
                  value={filePath}
                  onChange={(e) => setFilePath(e.target.value)}
                  placeholder="/path/to/your/file.csv"
                  className="w-full input font-mono"
                />
              </div>
              <button
                onClick={handleLoadPath}
                disabled={!filePath || loadPath.isPending}
                className="btn-primary w-full"
              >
                {loadPath.isPending ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Loading...
                  </span>
                ) : (
                  'Load File'
                )}
              </button>
            </div>
          )}

          {activeTab === 'folder' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-text-muted mb-2">Folder Path</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={folderPath}
                    onChange={(e) => setFolderPath(e.target.value)}
                    placeholder="/path/to/folder"
                    className="flex-1 input font-mono"
                  />
                  <button
                    onClick={handleScanFolder}
                    disabled={!folderPath || scanFolder.isPending}
                    className="btn-secondary"
                  >
                    {scanFolder.isPending ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      'Scan'
                    )}
                  </button>
                </div>
              </div>

              {scannedFiles.length > 0 && (
                <div className="border border-border-subtle rounded-lg overflow-hidden">
                  {scannedFiles.map((file, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 hover:bg-bg-elevated cursor-pointer border-b border-border-subtle last:border-0"
                      onClick={() => {
                        setFilePath(file.path)
                        setActiveTab('path')
                      }}
                    >
                      <div className="flex items-center gap-3">
                        <File className="w-4 h-4 text-text-muted" />
                        <span className="text-sm">{file.name}</span>
                      </div>
                      <span className="text-xs text-text-muted">
                        {file.size_mb.toFixed(1)} MB
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
