/**
 * Create Service Session Page
 * Form to create a new service session with person/service selection, date/time picker, and location/notes
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
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
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/sessions/new')({
  component: CreateSessionPage,
})

function CreateSessionPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [persons, setPersons] = useState<Array<{ id: string; name: string }>>([])
  const [services, setServices] = useState<Array<{ id: string; name: string }>>([])
  const [contracts, setContracts] = useState<Array<{ id: string; name: string }>>([])
  const [serviceProviders, setServiceProviders] = useState<Array<{ id: string; name: string }>>([])
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
    const fetchData = async () => {
      try {
        const [personsResponse, servicesResponse, contractsResponse, providersResponse] = await Promise.all([
          personsApi.list({ limit: 100 }),
          servicesApi.list({ limit: 100 }),
          contractsApi.list({ limit: 100 }),
          personsApi.list({ limit: 100, person_type: PersonType.SERVICE_PROVIDER }),
        ])
        setPersons(personsResponse.items.map(p => ({ 
          id: p.id, 
          name: `${p.first_name} ${p.last_name}`.trim() 
        })))
        setServices(servicesResponse.items.map(s => ({ id: s.id, name: s.name })))
        setContracts(contractsResponse.items.map(c => ({ 
          id: c.id, 
          name: c.contract_number || `Contract #${c.id.slice(0, 8)}` 
        })))
        setServiceProviders(providersResponse.items.map(p => ({ 
          id: p.id, 
          name: `${p.first_name} ${p.last_name}`.trim() 
        })))
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }
    fetchData()
  }, [])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.service_id) {
      newErrors.service_id = 'Service is required'
    }

    if (!formData.person_id) {
      newErrors.person_id = 'Person is required'
    }

    if (!formData.scheduled_date) {
      newErrors.scheduled_date = 'Scheduled date is required'
    }

    if (!formData.scheduled_time) {
      newErrors.scheduled_time = 'Scheduled time is required'
    }

    if (formData.scheduled_date && formData.scheduled_time) {
      const scheduledDateTime = new Date(`${formData.scheduled_date}T${formData.scheduled_time}`)
      const now = new Date()
      if (scheduledDateTime < now) {
        newErrors.scheduled_date = 'Scheduled date and time must be in the future'
      }
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
      const scheduledAt = new Date(`${formData.scheduled_date}T${formData.scheduled_time}`).toISOString()
      
      const sessionData: any = {
        service_id: formData.service_id,
        person_id: formData.person_id,
        scheduled_at: scheduledAt,
        service_provider_id: formData.service_provider_id || null,
        contract_id: formData.contract_id || null,
        location: formData.location.trim() || null,
        notes: formData.notes.trim() || null,
      }

      await serviceSessionsApi.create(sessionData)
      showSuccess('Session scheduled successfully')
      navigate({ to: '/sessions' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create session'
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

  const personOptions = [
    { value: '', label: 'Select person (required)' },
    ...persons.map(p => ({ value: p.id, label: p.name })),
  ]

  const serviceOptions = [
    { value: '', label: 'Select service (required)' },
    ...services.map(s => ({ value: s.id, label: s.name })),
  ]

  const contractOptions = [
    { value: '', label: 'Select contract (optional)' },
    ...contracts.map(c => ({ value: c.id, label: c.name })),
  ]

  const serviceProviderOptions = [
    { value: '', label: 'Select service provider (optional)' },
    ...serviceProviders.map(p => ({ value: p.id, label: p.name })),
  ]

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/sessions' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Sessions</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Schedule New Session</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Session Information</h2>

          <Select
            label="Service"
            name="service_id"
            value={formData.service_id}
            onChange={(value) => {
              setFormData({ ...formData, service_id: value as string })
              if (errors.service_id) setErrors({ ...errors, service_id: '' })
            }}
            options={serviceOptions}
            error={errors.service_id}
            required
            placeholder="Select service"
          />

          <Select
            label="Person"
            name="person_id"
            value={formData.person_id}
            onChange={(value) => {
              setFormData({ ...formData, person_id: value as string })
              if (errors.person_id) setErrors({ ...errors, person_id: '' })
            }}
            options={personOptions}
            error={errors.person_id}
            required
            placeholder="Select person"
          />

          <Select
            label="Service Provider"
            name="service_provider_id"
            value={formData.service_provider_id}
            onChange={(value) => setFormData({ ...formData, service_provider_id: value as string })}
            options={serviceProviderOptions}
            placeholder="Select service provider (optional)"
          />

          <Select
            label="Contract"
            name="contract_id"
            value={formData.contract_id}
            onChange={(value) => setFormData({ ...formData, contract_id: value as string })}
            options={contractOptions}
            placeholder="Select contract (optional)"
          />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Schedule</h2>

          <div className="grid grid-cols-2 gap-4">
            <DatePicker
              label="Date"
              name="scheduled_date"
              value={formData.scheduled_date}
              onChange={(value) => {
                setFormData({ ...formData, scheduled_date: value })
                if (errors.scheduled_date) setErrors({ ...errors, scheduled_date: '' })
              }}
              error={errors.scheduled_date}
              required
            />

            <FormField
              label="Time"
              name="scheduled_time"
              type="time"
              value={formData.scheduled_time}
              onChange={(e) => {
                setFormData({ ...formData, scheduled_time: e.target.value })
                if (errors.scheduled_time) setErrors({ ...errors, scheduled_time: '' })
              }}
              error={errors.scheduled_time}
              required
            />
          </div>

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Additional Information</h2>

          <FormField
            label="Location"
            name="location"
            value={formData.location}
            onChange={(e) => setFormData({ ...formData, location: e.target.value })}
            placeholder="Enter session location (optional)"
          />

          <FormField
            label="Notes"
            name="notes"
            type="textarea"
            value={formData.notes}
            onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            placeholder="Enter any additional notes (optional)"
            rows={4}
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
                  Scheduling...
                </span>
              ) : (
                'Schedule Session'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/sessions' })}
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
