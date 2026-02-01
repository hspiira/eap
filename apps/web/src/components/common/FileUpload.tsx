/**
 * File Upload Component
 * Reusable file upload component with drag-and-drop support
 */

import { useState, useRef } from 'react'
import { Upload, X, File } from 'lucide-react'

interface FileUploadProps {
  label?: string
  name: string
  value?: File | null
  onChange: (file: File | null) => void
  accept?: string
  maxSize?: number // in bytes
  error?: string
  required?: boolean
  disabled?: boolean
  className?: string
}

export function FileUpload({
  label,
  name,
  value,
  onChange,
  accept,
  maxSize,
  error,
  required = false,
  disabled = false,
  className = '',
}: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false)
  const [dragError, setDragError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const validateFile = (file: File): string | null => {
    if (maxSize && file.size > maxSize) {
      return `File size must be less than ${formatFileSize(maxSize)}`
    }
    return null
  }

  const handleFileSelect = (file: File) => {
    const validationError = validateFile(file)
    if (validationError) {
      setDragError(validationError)
      return
    }
    setDragError(null)
    onChange(file)
  }

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)

    if (disabled) return

    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    if (!disabled) {
      setIsDragging(true)
    }
  }

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (files && files.length > 0) {
      handleFileSelect(files[0])
    }
  }

  const handleRemove = () => {
    onChange(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
    setDragError(null)
  }

  const handleClick = () => {
    if (!disabled && fileInputRef.current) {
      fileInputRef.current.click()
    }
  }

  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label className="block text-text text-sm font-medium mb-2">
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
      )}

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={handleClick}
        className={`
          relative border-2 border-dashed rounded-none transition-colors cursor-pointer
          ${isDragging ? 'border-primary bg-primary/10' : 'border-border'}
          ${error || dragError ? 'border-danger' : ''}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-primary'}
          ${value ? 'bg-surface' : 'bg-surface-muted'}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          name={name}
          accept={accept}
          onChange={handleInputChange}
          disabled={disabled}
          required={required}
          className="hidden"
        />

        {value ? (
          <div className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <File size={24} className="text-primary" />
              <div>
                <p className="text-text font-medium">{value.name}</p>
                <p className="text-text-muted text-sm">{formatFileSize(value.size)}</p>
              </div>
            </div>
            {!disabled && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation()
                  handleRemove()
                }}
                className="p-1 hover:bg-surface-hover rounded-none transition-colors"
                aria-label="Remove file"
              >
                <X size={18} className="text-nurturing" />
              </button>
            )}
          </div>
        ) : (
          <div className="p-6 text-center">
            <Upload size={32} className="mx-auto mb-2 text-text-muted" />
            <p className="text-text mb-1">
              <span className="text-primary hover:text-primary-hover">Click to upload</span> or drag and drop
            </p>
            <p className="text-text-muted text-sm">
              {accept ? `Accepted: ${accept}` : 'Any file type'}
              {maxSize && ` • Max size: ${formatFileSize(maxSize)}`}
            </p>
          </div>
        )}
      </div>

      {(error || dragError) && (
        <p className="mt-1 text-sm text-danger">{error || dragError}</p>
      )}
    </div>
  )
}
