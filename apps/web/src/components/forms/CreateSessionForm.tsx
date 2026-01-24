/**
 * Create Session Form (Schedule Session)
 * Used inside CreateModal on sessions list page
 */

import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { serviceSessionsApi } from '@/api/endpoints/service-sessions'
import { personsApi } from '@/api/endpoints/persons'
import { servicesApi } from '@/api/endpoints/services'
import { contractsApi } from '@/api/endpoints/contracts'
import { PersonType } from '@/types/enums'

export interface CreateSessionFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateSessionForm({ onSuccess, onCancel, onLoadingChange }: CreateSessionFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [persons, setPersons] = useState<Array<{ id: string; name: string }>>([])
  const [services, setServices] = useState<Array<{ id: string; name: string }>>([])
  const [contracts, setContracts] = useState<Array<{ id: string; name: string }>>([])
  const [providers, setProviders] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    service_id: '',
    person_id: '',
    service_provider_id: '',
    contract_id: '',
    scheduled_date: '',
    scheduled_time: '',
    location: '',
    notes: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const load = async () => {
      try {
        const [p, s, c, pr] = await Promise.all([
          personsApi.list({ limit: 100 }),
          servicesApi.list({ limit: 100 }),
          contractsApi.list({ limit: 100 }),
          personsApi.list({ limit: 100, person_type: PersonType.SERVICE_PROVIDER }),
        ])
        setPersons(p.items.map((x) => ({ id: x.id, name: `${x.first_name} ${x.last_name}`.trim() })))
        setServices(s.items.map((x) => ({ id: x.id, name: x.name })))
        setContracts(c.items.map((x) => ({ id: x.id, name: x.contract_number || `#${x.id.slice(0, 8)}` })))
        setProviders(pr.items.map((x) => ({ id: x.id, name: `${x.first_name} ${x.last_name}`.trim() })))
      } catch (e) {
        console.error(e)
      }
    }
    load()
  }, [])

  const setLoadingState = (v: boolean) => { setLoading(v); onLoadingChange?.(v) }

  const validate = () => {
    const next: Record<string, string> = {}
    if (!formData.service_id) next.service_id = 'Service is required'
    if (!formData.person_id) next.person_id = 'Person is required'
    if (!formData.scheduled_date) next.scheduled_date = 'Date is required'
    if (!formData.scheduled_time) next.scheduled_time = 'Time is required'
    if (formData.scheduled_date && formData.scheduled_time) {
      const at = new Date(`${formData.scheduled_date}T${formData.scheduled_time}`)
      if (at < new Date()) next.scheduled_date = 'Date & time must be in the future'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validate()) return
    try {
      setLoadingState(true)
      const scheduledAt = new Date(`${formData.scheduled_date}T${formData.scheduled_time}`).toISOString()
      await serviceSessionsApi.create({
        service_id: formData.service_id,
        person_id: formData.person_id,
        service_provider_id: formData.service_provider_id || null,
        contract_id: formData.contract_id || null,
        scheduled_at: scheduledAt,
        location: formData.location.trim() || null,
        notes: formData.notes.trim() || null,
      })
      showSuccess('Session scheduled successfully')
      onSuccess()
    } catch (err: any) {
      showError(err.message || 'Failed to create session')
      if (err.details) { const m: Record<string, string> = {}; err.details.forEach((d: any) => { if (d.field) m[d.field] = d.message }); setErrors(m) }
    } finally {
      setLoadingState(false)
    }
  }

  const personOpts = [{ value: '', label: 'Select person (required)' }, ...persons.map((x) => ({ value: x.id, label: x.name }))]
  const serviceOpts = [{ value: '', label: 'Select service (required)' }, ...services.map((x) => ({ value: x.id, label: x.name }))]
  const contractOpts = [{ value: '', label: 'Select contract (optional)' }, ...contracts.map((x) => ({ value: x.id, label: x.name }))]
  const providerOpts = [{ value: '', label: 'Select provider (optional)' }, ...providers.map((x) => ({ value: x.id, label: x.name }))]

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-safe">Session Information</h3>
      <Select label="Service" name="service_id" value={formData.service_id} onChange={(v) => { setFormData({ ...formData, service_id: v as string }); if (errors.service_id) setErrors({ ...errors, service_id: '' }) }} options={serviceOpts} error={errors.service_id} required placeholder="Select service" />
      <Select label="Person" name="person_id" value={formData.person_id} onChange={(v) => { setFormData({ ...formData, person_id: v as string }); if (errors.person_id) setErrors({ ...errors, person_id: '' }) }} options={personOpts} error={errors.person_id} required placeholder="Select person" />
      <Select label="Service Provider" name="service_provider_id" value={formData.service_provider_id} onChange={(v) => setFormData({ ...formData, service_provider_id: v as string })} options={providerOpts} placeholder="Optional" />
      <Select label="Contract" name="contract_id" value={formData.contract_id} onChange={(v) => setFormData({ ...formData, contract_id: v as string })} options={contractOpts} placeholder="Optional" />

      <h3 className="text-sm font-semibold text-safe mt-4">Schedule</h3>
      <div className="grid grid-cols-2 gap-4">
        <DatePicker label="Date" name="scheduled_date" value={formData.scheduled_date} onChange={(v) => { setFormData({ ...formData, scheduled_date: v }); if (errors.scheduled_date) setErrors({ ...errors, scheduled_date: '' }) }} error={errors.scheduled_date} required />
        <FormField label="Time" name="scheduled_time" type="time" value={formData.scheduled_time} onChange={(e) => { setFormData({ ...formData, scheduled_time: e.target.value }); if (errors.scheduled_time) setErrors({ ...errors, scheduled_time: '' }) }} error={errors.scheduled_time} required />
      </div>

      <h3 className="text-sm font-semibold text-safe mt-4">Additional</h3>
      <FormField label="Location" name="location" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} placeholder="Optional" />
      <FormField label="Notes" name="notes" type="textarea" rows={4} value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} placeholder="Optional" />

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Scheduling...</span> : 'Schedule Session'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
