import { useState, useCallback } from 'react'
import { Upload, FileSpreadsheet, FileText, X } from 'lucide-react'

interface FileUploaderProps {
  onUpload: (file: File) => void
  isLoading?: boolean
  accept?: string
}

export function FileUploader({ 
  onUpload, 
  isLoading = false,
  accept = '.csv,.xlsx,.xls' 
}: FileUploaderProps) {
  const [isDragOver, setIsDragOver] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(false)
    
    const files = e.dataTransfer.files
    if (files.length > 0) {
      const file = files[0]
      if (file.name.match(/\.(csv|xlsx|xls)$/i)) {
        setSelectedFile(file)
        onUpload(file)
      }
    }
  }, [onUpload])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      setSelectedFile(files[0])
      onUpload(files[0])
    }
  }, [onUpload])

  const clearFile = useCallback(() => {
    setSelectedFile(null)
  }, [])

  const getFileIcon = (filename: string) => {
    if (filename.endsWith('.csv')) return <FileText className="w-8 h-8 text-accent-green" />
    return <FileSpreadsheet className="w-8 h-8 text-accent-blue" />
  }

  if (selectedFile) {
    return (
      <div className="card p-6">
        <div className="flex items-center gap-4">
          {getFileIcon(selectedFile.name)}
          <div className="flex-1 min-w-0">
            <p className="font-medium text-text-primary truncate">{selectedFile.name}</p>
            <p className="text-sm text-text-muted">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>
          {!isLoading && (
            <button 
              onClick={clearFile}
              className="p-2 hover:bg-bg-elevated rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-text-muted" />
            </button>
          )}
        </div>
        {isLoading && (
          <div className="mt-4 flex items-center gap-2 text-accent-cyan">
            <div className="w-4 h-4 border-2 border-accent-cyan/30 border-t-accent-cyan rounded-full animate-spin" />
            <span className="text-sm">Uploading...</span>
          </div>
        )}
      </div>
    )
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`upload-zone ${isDragOver ? 'dragover' : ''}`}
    >
      <input
        type="file"
        accept={accept}
        onChange={handleFileSelect}
        className="hidden"
        id="file-upload"
      />
      <label htmlFor="file-upload" className="cursor-pointer block">
        <div className="text-5xl mb-4">📂</div>
        <h3 className="text-lg font-semibold text-text-primary mb-2">
          Upload Your Dataset
        </h3>
        <p className="text-text-muted text-sm mb-4">
          CSV · XLSX · XLS &nbsp;•&nbsp; Up to 200 MB
        </p>
        <div className="flex items-center justify-center gap-2 text-accent-blue">
          <Upload className="w-4 h-4" />
          <span className="text-sm">Click or drag to upload</span>
        </div>
      </label>
    </div>
  )
}
