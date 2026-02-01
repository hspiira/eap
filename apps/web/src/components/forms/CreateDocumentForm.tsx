/**
 * Create Document Form
 * Used inside CreateModal on documents list page
 */

import { useState } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { FileUpload } from '@/components/common/FileUpload'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { documentsApi } from '@/api/endpoints/documents'
import { DocumentType } from '@/types/enums'

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

export interface CreateDocumentFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateDocumentForm({ onSuccess, onCancel, onLoadingChange }: CreateDocumentFormProps) {
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

  const setLoadingState = (v: boolean) => {
    setLoading(v)
    onLoadingChange?.(v)
  }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.name.trim()) next.name = 'Document name is required'
    if (!formData.document_type) next.document_type = 'Document type is required'
    if (!formData.file) next.file = 'File is required'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      setLoadingState(true)
      await documentsApi.create({
        name: formData.name.trim(),
        document_type: formData.document_type as DocumentType,
        file: formData.file!,
        confidentiality_level: formData.confidentiality_level || null,
        expiry_date: formData.expiry_date || null,
      })
      showSuccess('Document uploaded successfully')
      onSuccess()
    } catch (err: any) {
      showError(err.message || 'Failed to upload document')
      if (err.details) {
        const map: Record<string, string> = {}
        err.details.forEach((d: any) => { if (d.field) map[d.field] = d.message })
        setErrors(map)
      }
    } finally {
      setLoadingState(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-safe">Document Information</h3>
      <FormField
        label="Document Name"
        name="name"
        value={formData.name}
        onChange={(e) => { setFormData({ ...formData, name: e.target.value }); if (errors.name) setErrors({ ...errors, name: '' }) }}
        error={errors.name}
        required
        placeholder="Enter document name"
      />
      <Select
        label="Document Type"
        name="document_type"
        value={formData.document_type}
        onChange={(v) => { setFormData({ ...formData, document_type: v as DocumentType }); if (errors.document_type) setErrors({ ...errors, document_type: '' }) }}
        options={documentTypeOptions}
        error={errors.document_type}
        required
        placeholder="Select document type"
      />
      <FileUpload
        label="File"
        name="file"
        value={formData.file}
        onChange={(file) => { setFormData({ ...formData, file }); if (errors.file) setErrors({ ...errors, file: '' }) }}
        error={errors.file}
        required
        maxSize={MAX_FILE_SIZE}
        accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.jpg,.jpeg,.png"
      />

      <h3 className="text-sm font-semibold text-safe mt-4">Security & Metadata</h3>
      <Select
        label="Confidentiality Level"
        name="confidentiality_level"
        value={formData.confidentiality_level}
        onChange={(v) => setFormData({ ...formData, confidentiality_level: v as string })}
        options={confidentialityOptions}
        placeholder="Optional"
      />
      <DatePicker label="Expiry Date" name="expiry_date" value={formData.expiry_date} onChange={(v) => setFormData({ ...formData, expiry_date: v })} />

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Uploading...</span> : 'Upload Document'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
