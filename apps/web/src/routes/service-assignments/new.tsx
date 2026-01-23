/**
 * Create Service Assignment Page
 * Form to create a new service assignment linking a service to a contract
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { serviceAssignmentsApi } from '@/api/endpoints/service-assignments'
import { contractsApi } from '@/api/endpoints/contracts'
import { servicesApi } from '@/api/endpoints/services'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/service-assignments/new')({
  component: CreateServiceAssignmentPage,
})

function CreateServiceAssignmentPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [contracts, setContracts] = useState<Array<{ id: string; name: string }>>([])
  const [services, setServices] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    contract_id: '',
    service_id: '',
    start_date: '',
    end_date: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [contractsResponse, servicesResponse] = await Promise.all([
          contractsApi.list({ limit: 100 }),
          servicesApi.list({ limit: 100 }),
        ])
        setContracts(contractsResponse.items.map(c => ({ 
          id: c.id, 
          name: c.contract_number || `Contract #${c.id.slice(0, 8)}` 
        })))
        setServices(servicesResponse.items.map(s => ({ id: s.id, name: s.name })))
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }
    fetchData()
  }, [])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.contract_id) {
      newErrors.contract_id = 'Contract is required'
    }

    if (!formData.service_id) {
      newErrors.service_id = 'Service is required'
    }

    if (formData.end_date && formData.start_date) {
      const start = new Date(formData.start_date)
      const end = new Date(formData.end_date)
      if (end < start) {
        newErrors.end_date = 'End date must be after start date'
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
      const assignmentData: any = {
        contract_id: formData.contract_id,
        service_id: formData.service_id,
        start_date: formData.start_date || null,
        end_date: formData.end_date || null,
      }

      await serviceAssignmentsApi.create(assignmentData)
      showSuccess('Service assignment created successfully')
      navigate({ to: '/service-assignments' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create assignment'
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

  const contractOptions = [
    { value: '', label: 'Select contract (required)' },
    ...contracts.map(c => ({ value: c.id, label: c.name })),
  ]

  const serviceOptions = [
    { value: '', label: 'Select service (required)' },
    ...services.map(s => ({ value: s.id, label: s.name })),
  ]

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/service-assignments' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Service Assignments</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create Service Assignment</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Assignment Information</h2>

          <Select
            label="Contract"
            name="contract_id"
            value={formData.contract_id}
            onChange={(value) => {
              setFormData({ ...formData, contract_id: value as string })
              if (errors.contract_id) setErrors({ ...errors, contract_id: '' })
            }}
            options={contractOptions}
            error={errors.contract_id}
            required
            placeholder="Select contract"
          />

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

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Date Information</h2>

          <DatePicker
            label="Start Date"
            name="start_date"
            value={formData.start_date}
            onChange={(value) => {
              setFormData({ ...formData, start_date: value })
              if (errors.start_date) setErrors({ ...errors, start_date: '' })
            }}
            error={errors.start_date}
          />

          <DatePicker
            label="End Date"
            name="end_date"
            value={formData.end_date}
            onChange={(value) => {
              setFormData({ ...formData, end_date: value })
              if (errors.end_date) setErrors({ ...errors, end_date: '' })
            }}
            error={errors.end_date}
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
                  Creating...
                </span>
              ) : (
                'Create Assignment'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/service-assignments' })}
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
