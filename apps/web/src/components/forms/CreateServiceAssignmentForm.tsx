/**
 * Create Service Assignment Form
 * Used inside CreateModal on service-assignments list page
 */

import { useState, useEffect } from 'react'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { serviceAssignmentsApi } from '@/api/endpoints/service-assignments'
import { contractsApi } from '@/api/endpoints/contracts'
import { servicesApi } from '@/api/endpoints/services'

export interface CreateServiceAssignmentFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateServiceAssignmentForm({ onSuccess, onCancel, onLoadingChange }: CreateServiceAssignmentFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [contracts, setContracts] = useState<Array<{ id: string; name: string }>>([])
  const [services, setServices] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({ contract_id: '', service_id: '', start_date: '', end_date: '' })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const load = async () => {
      try {
        const [c, s] = await Promise.all([contractsApi.list({ limit: 100 }), servicesApi.list({ limit: 100 })])
        setContracts(c.items.map((x) => ({ id: x.id, name: x.contract_number || `#${x.id.slice(0, 8)}` })))
        setServices(s.items.map((x) => ({ id: x.id, name: x.name })))
      } catch (e) {
        console.error(e)
      }
    }
    load()
  }, [])

  const setLoadingState = (v: boolean) => { setLoading(v); onLoadingChange?.(v) }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.contract_id) next.contract_id = 'Contract is required'
    if (!formData.service_id) next.service_id = 'Service is required'
    if (formData.end_date && formData.start_date && new Date(formData.end_date) < new Date(formData.start_date)) next.end_date = 'End date must be after start date'
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return
    try {
      setLoadingState(true)
      await serviceAssignmentsApi.create({
        contract_id: formData.contract_id,
        service_id: formData.service_id,
        start_date: formData.start_date || null,
        end_date: formData.end_date || null,
      })
      showSuccess('Service assignment created successfully')
      onSuccess()
    } catch (err: any) {
      showError(err.message || 'Failed to create assignment')
      if (err.details) { const m: Record<string, string> = {}; err.details.forEach((d: any) => { if (d.field) m[d.field] = d.message }); setErrors(m) }
    } finally {
      setLoadingState(false)
    }
  }

  const contractOptions = [{ value: '', label: 'Select contract (required)' }, ...contracts.map((c) => ({ value: c.id, label: c.name }))]
  const serviceOptions = [{ value: '', label: 'Select service (required)' }, ...services.map((s) => ({ value: s.id, label: s.name }))]

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-safe">Assignment Information</h3>
      <Select label="Contract" name="contract_id" value={formData.contract_id} onChange={(v) => { setFormData({ ...formData, contract_id: v as string }); if (errors.contract_id) setErrors({ ...errors, contract_id: '' }) }} options={contractOptions} error={errors.contract_id} required placeholder="Select contract" />
      <Select label="Service" name="service_id" value={formData.service_id} onChange={(v) => { setFormData({ ...formData, service_id: v as string }); if (errors.service_id) setErrors({ ...errors, service_id: '' }) }} options={serviceOptions} error={errors.service_id} required placeholder="Select service" />
      <DatePicker label="Start Date" name="start_date" value={formData.start_date} onChange={(v) => setFormData({ ...formData, start_date: v })} />
      <DatePicker label="End Date" name="end_date" value={formData.end_date} onChange={(v) => { setFormData({ ...formData, end_date: v }); if (errors.end_date) setErrors({ ...errors, end_date: '' }) }} error={errors.end_date} />

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create Assignment'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
