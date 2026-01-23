/**
 * Create Document Page
 * Form to create a new document with file upload, metadata form, and document type selection
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { FileUpload } from '@/components/common/FileUpload'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { documentsApi } from '@/api/endpoints/documents'
import { DocumentType } from '@/types/enums'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/documents/new')({
  component: CreateDocumentPage,
})

const documentTypeOptions = [
  { value: '', label: 'Select document type (required)' },
  { value: DocumentType.CONTRACT, label: 'Contract' },
  { value: DocumentType.CERTIFICATION, label: 'Certification' },
  { value: DocumentType.KPI_REPORT, label: 'KPI Report' },
  { value: DocumentType.FEEDBACK_SUMMARY, label: 'Feedback Summary' },
  { value: DocumentType.BILLING_REPORT, label: 'Billing Report' },
  { value: DocumentType.UTILIZATION_REPORT, label: 'Utilization Report' },
  { value: DocumentType.OTHER, label: 'Other' },
]

const confidentialityOptions = [
  { value: '', label: 'Select confidentiality level (optional)' },
  { value: 'Public', label: 'Public' },
  { value: 'Internal', label: 'Internal' },
  { value: 'Confidential', label: 'Confidential' },
  { value: 'Restricted', label: 'Restricted' },
]

const MAX_FILE_SIZE = 50 * 1024 * 1024 // 50 MB

function CreateDocumentPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    document_type: '' as DocumentType | '',
    file: null as File | null,
    confidentiality_level: '',
    expiry_date: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'Document name is required'
    }

    if (!formData.document_type) {
      newErrors.document_type = 'Document type is required'
    }

    if (!formData.file) {
      newErrors.file = 'File is required'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!validateForm()) {
      return
    }

    try {
      setLoading(true)
      const documentData: any = {
        name: formData.name.trim(),
        document_type: formData.document_type as DocumentType,
        file: formData.file,
        confidentiality_level: formData.confidentiality_level || null,
        expiry_date: formData.expiry_date || null,
      }

      await documentsApi.create(documentData)
      showSuccess('Document uploaded successfully')
      navigate({ to: '/documents' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to upload document'
      showError(errorMessage)
      if (error.details) {
        const fieldErrors: Record<string, string> = {}
        error.details.forEach((detail: any) => {
          if (detail.field) {
            fieldErrors[detail.field] = detail.message
          }
        })
        setErrors(fieldErrors)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/documents' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Documents</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Upload New Document</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Document Information</h2>

          <FormField
            label="Document Name"
            name="name"
            value={formData.name}
            onChange={(e) => {
              setFormData({ ...formData, name: e.target.value })
              if (errors.name) setErrors({ ...errors, name: '' })
            }}
            error={errors.name}
            required
            placeholder="Enter document name"
          />

          <Select
            label="Document Type"
            name="document_type"
            value={formData.document_type}
            onChange={(value) => {
              setFormData({ ...formData, document_type: value as DocumentType })
              if (errors.document_type) setErrors({ ...errors, document_type: '' })
            }}
            options={documentTypeOptions}
            error={errors.document_type}
            required
            placeholder="Select document type"
          />

          <FileUpload
            label="File"
            name="file"
            value={formData.file}
            onChange={(file) => {
              setFormData({ ...formData, file })
              if (errors.file) setErrors({ ...errors, file: '' })
            }}
            error={errors.file}
            required
            maxSize={MAX_FILE_SIZE}
            accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png"
          />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Security & Metadata</h2>

          <Select
            label="Confidentiality Level"
            name="confidentiality_level"
            value={formData.confidentiality_level}
            onChange={(value) => setFormData({ ...formData, confidentiality_level: value as string })}
            options={confidentialityOptions}
            placeholder="Select confidentiality level (optional)"
          />

          <DatePicker
            label="Expiry Date"
            name="expiry_date"
            value={formData.expiry_date}
            onChange={(value) => setFormData({ ...formData, expiry_date: value })}
          />

          <div className="flex gap-3 mt-6">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <LoadingSpinner size="sm" color="white" />
                  Uploading...
                </span>
              ) : (
                'Upload Document'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/documents' })}
              className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </AppLayout>
  )
}
