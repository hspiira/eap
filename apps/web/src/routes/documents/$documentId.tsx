/**
 * Document Detail Page
 * Displays document information, version history, download, publish, confidentiality, expiry, and lifecycle actions
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { StatusBadge } from '@/components/common/StatusBadge'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { ErrorDisplay } from '@/components/common/ErrorDisplay'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { ConfirmDialog } from '@/components/common/ConfirmDialog'
import { useToast } from '@/contexts/ToastContext'
import { documentsApi } from '@/api/endpoints/documents'
import type { Document } from '@/types/entities'
import type { DocumentStatus, DocumentType } from '@/types/enums'
import { FileText, Download, Eye, Lock, Calendar, Clock, History, Edit, Archive } from 'lucide-react'

export const Route = createFileRoute('/documents/$documentId')({
  component: DocumentDetailPage,
})

function DocumentDetailPage() {
  const { documentId } = Route.useParams()
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [document, setDocument] = useState<Document | null>(null)
  const [versions, setVersions] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showConfidentialityDialog, setShowConfidentialityDialog] = useState(false)
  const [showExpiryDialog, setShowExpiryDialog] = useState(false)
  const [confidentialityLevel, setConfidentialityLevel] = useState('')
  const [expiryDate, setExpiryDate] = useState('')

  const fetchDocument = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await documentsApi.getById(documentId)
      setDocument(data)
      
      // Fetch versions
      try {
        const versionsData = await documentsApi.getVersions(documentId)
        setVersions(versionsData.sort((a, b) => (b.version || 0) - (a.version || 0)))
      } catch (err) {
        console.error('Error fetching versions:', err)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load document')
      showError('Failed to load document')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDocument()
  }, [documentId])

  const handleDownload = async () => {
    try {
      setActionLoading(true)
      const blob = await documentsApi.download(documentId)
      const url = window.URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url
      a.download = document?.name || 'document'
      window.document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      window.document.body.removeChild(a)
      showSuccess('Document downloaded successfully')
    } catch (err: any) {
      showError(`Failed to download document: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handlePublish = async () => {
    try {
      setActionLoading(true)
      const updatedDocument = await documentsApi.publish(documentId)
      setDocument(updatedDocument)
      showSuccess('Document published successfully')
    } catch (err: any) {
      showError(`Failed to publish document: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleArchive = async () => {
    try {
      setActionLoading(true)
      const updatedDocument = await documentsApi.archive(documentId)
      setDocument(updatedDocument)
      showSuccess('Document archived successfully')
    } catch (err: any) {
      showError(`Failed to archive document: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleSetConfidentiality = async () => {
    if (!confidentialityLevel) {
      showError('Please select a confidentiality level')
      return
    }

    try {
      setActionLoading(true)
      const updatedDocument = await documentsApi.setConfidentiality(documentId, {
        confidentiality_level: confidentialityLevel,
      })
      setDocument(updatedDocument)
      setShowConfidentialityDialog(false)
      setConfidentialityLevel('')
      showSuccess('Confidentiality level updated successfully')
    } catch (err: any) {
      showError(`Failed to update confidentiality: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  const handleSetExpiry = async () => {
    try {
      setActionLoading(true)
      const updatedDocument = await documentsApi.setExpiry(documentId, {
        expiry_date: expiryDate || null,
      })
      setDocument(updatedDocument)
      setShowExpiryDialog(false)
      setExpiryDate('')
      showSuccess('Expiry date updated successfully')
    } catch (err: any) {
      showError(`Failed to update expiry date: ${err.message || 'Unknown error'}`)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-center p-12">
            <LoadingSpinner size="lg" />
          </div>
        </div>
      </AppLayout>
    )
  }

  if (error || !document) {
    return (
      <AppLayout>
        <div className="max-w-7xl mx-auto">
          <ErrorDisplay
            error={error || 'Document not found'}
            onRetry={fetchDocument}
          />
        </div>
      </AppLayout>
    )
  }

  const formatFileSize = (bytes: number | null | undefined) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const formatDate = (date: string | null | undefined) => {
    if (!date) return '-'
    return new Date(date).toLocaleString()
  }

  const confidentialityOptions = [
    { value: 'Public', label: 'Public' },
    { value: 'Internal', label: 'Internal' },
    { value: 'Confidential', label: 'Confidential' },
    { value: 'Restricted', label: 'Restricted' },
  ]

  const isExpired = document.expiry_date && new Date(document.expiry_date) < new Date()
  const canPublish = document.status === 'Draft'
  const canArchive = document.status !== 'Archived'

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-safe mb-2">{document.name}</h1>
            <div className="flex items-center gap-4">
              <StatusBadge status={document.status as DocumentStatus} />
              {isExpired && (
                <span className="text-danger text-sm font-medium">Expired</span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-3">
            {document.file_path && (
              <button
                onClick={handleDownload}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <Download size={18} />
                <span>Download</span>
              </button>
            )}
            {canPublish && (
              <button
                onClick={handlePublish}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <Eye size={18} />
                <span>Publish</span>
              </button>
            )}
            {canArchive && (
              <button
                onClick={handleArchive}
                disabled={actionLoading}
                className="flex items-center gap-2 px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors disabled:opacity-50"
              >
                <Archive size={18} />
                <span>Archive</span>
              </button>
            )}
            <button
              onClick={() => navigate({ to: `/documents/${documentId}/edit` })}
              className="flex items-center gap-2 px-4 py-2 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors"
            >
              <Edit size={18} />
              <span>Edit</span>
            </button>
          </div>
        </div>

        {/* Document Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* Document Details */}
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <FileText size={20} />
              Document Details
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Name</dt>
                <dd className="text-safe mt-1">{document.name}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Type</dt>
                <dd className="text-safe mt-1">{document.document_type}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Status</dt>
                <dd className="text-safe mt-1">
                  <StatusBadge status={document.status as DocumentStatus} size="sm" />
                </dd>
              </div>
              {document.version && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Version</dt>
                  <dd className="text-safe mt-1">v{document.version}</dd>
                </div>
              )}
              {document.file_size && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">File Size</dt>
                  <dd className="text-safe mt-1">{formatFileSize(document.file_size)}</dd>
                </div>
              )}
              {document.mime_type && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">MIME Type</dt>
                  <dd className="text-safe mt-1">{document.mime_type}</dd>
                </div>
              )}
            </dl>
          </div>

          {/* Security & Dates */}
          <div className="bg-white border border-[0.5px] border-safe/30 p-6">
            <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
              <Lock size={20} />
              Security & Dates
            </h2>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-safe-light">Confidentiality Level</dt>
                <dd className="text-safe mt-1 flex items-center gap-2">
                  {document.confidentiality_level || 'Not set'}
                  <button
                    onClick={() => {
                      setConfidentialityLevel(document.confidentiality_level || '')
                      setShowConfidentialityDialog(true)
                    }}
                    className="text-natural hover:text-natural-dark text-sm"
                  >
                    <Edit size={14} />
                  </button>
                </dd>
              </div>
              {document.expiry_date && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Expiry Date</dt>
                  <dd className={`mt-1 flex items-center gap-2 ${isExpired ? 'text-danger' : 'text-safe'}`}>
                    <Calendar size={16} />
                    {formatDate(document.expiry_date)}
                    {isExpired && <span className="text-xs">(Expired)</span>}
                  </dd>
                </div>
              )}
              {document.published_at && (
                <div>
                  <dt className="text-sm font-medium text-safe-light">Published At</dt>
                  <dd className="text-safe mt-1 flex items-center gap-2">
                    <Clock size={16} />
                    {formatDate(document.published_at)}
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-sm font-medium text-safe-light">Created</dt>
                <dd className="text-safe mt-1">{formatDate(document.created_at)}</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-safe-light">Last Updated</dt>
                <dd className="text-safe mt-1">{formatDate(document.updated_at)}</dd>
              </div>
              {!document.expiry_date && (
                <div>
                  <button
                    onClick={() => {
                      setExpiryDate('')
                      setShowExpiryDialog(true)
                    }}
                    className="text-natural hover:text-natural-dark text-sm flex items-center gap-1"
                  >
                    <Calendar size={14} />
                    Set Expiry Date
                  </button>
                </div>
              )}
            </dl>
          </div>

          {/* Version History */}
          {versions.length > 0 && (
            <div className="bg-white border border-[0.5px] border-safe/30 p-6 md:col-span-2">
              <h2 className="text-lg font-semibold text-safe mb-4 flex items-center gap-2">
                <History size={20} />
                Version History
              </h2>
              <div className="space-y-2">
                {versions.map((version) => (
                  <div
                    key={version.id}
                    className="flex items-center justify-between p-3 bg-safe-light/5 border border-[0.5px] border-safe/30"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-medium">v{version.version || 1}</span>
                      <span className="text-safe-light text-sm">
                        {formatDate(version.created_at)}
                      </span>
                      {version.file_size && (
                        <span className="text-safe-light text-sm">
                          {formatFileSize(version.file_size)}
                        </span>
                      )}
                    </div>
                    {version.id === document.id && (
                      <StatusBadge status="Active" size="sm" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Confidentiality Dialog */}
        {showConfidentialityDialog && (
          <ConfirmDialog
            title="Set Confidentiality Level"
            message="Select the confidentiality level for this document"
            onConfirm={handleSetConfidentiality}
            onCancel={() => {
              setShowConfidentialityDialog(false)
              setConfidentialityLevel('')
            }}
            confirmText="Update"
            cancelText="Cancel"
            loading={actionLoading}
          >
            <div className="mt-4">
              <Select
                label="Confidentiality Level"
                name="confidentiality_level"
                value={confidentialityLevel}
                onChange={(value) => setConfidentialityLevel(value as string)}
                options={[
                  { value: '', label: 'Select level' },
                  ...confidentialityOptions,
                ]}
                required
              />
            </div>
          </ConfirmDialog>
        )}

        {/* Expiry Date Dialog */}
        {showExpiryDialog && (
          <ConfirmDialog
            title="Set Expiry Date"
            message="Set an expiry date for this document (optional)"
            onConfirm={handleSetExpiry}
            onCancel={() => {
              setShowExpiryDialog(false)
              setExpiryDate('')
            }}
            confirmText="Update"
            cancelText="Cancel"
            loading={actionLoading}
          >
            <div className="mt-4">
              <DatePicker
                label="Expiry Date"
                name="expiry_date"
                value={expiryDate}
                onChange={setExpiryDate}
              />
              <button
                onClick={() => setExpiryDate('')}
                className="mt-2 text-sm text-nurturing hover:text-nurturing-dark"
              >
                Clear expiry date
              </button>
            </div>
          </ConfirmDialog>
        )}
      </div>
    </AppLayout>
  )
}
