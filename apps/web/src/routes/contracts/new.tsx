/**
 * Create Contract Page
 * Form to create a new contract with client selection, billing configuration, and date ranges
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState, useEffect } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { contractsApi } from '@/api/endpoints/contracts'
import { clientsApi } from '@/api/endpoints/clients'
import type { PaymentFrequency, PaymentStatus } from '@/types/enums'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/contracts/new')({
  component: CreateContractPage,
})

const billingFrequencyOptions = [
  { value: '', label: 'Select frequency (optional)' },
  { value: 'Weekly', label: 'Weekly' },
  { value: 'Monthly', label: 'Monthly' },
  { value: 'Quarterly', label: 'Quarterly' },
  { value: 'Annually', label: 'Annually' },
]

const paymentStatusOptions = [
  { value: '', label: 'Select status (optional)' },
  { value: 'Pending', label: 'Pending' },
  { value: 'Paid', label: 'Paid' },
  { value: 'Overdue', label: 'Overdue' },
  { value: 'Cancelled', label: 'Cancelled' },
  { value: 'Refunded', label: 'Refunded' },
]

const currencyOptions = [
  { value: 'USD', label: 'USD - US Dollar' },
  { value: 'EUR', label: 'EUR - Euro' },
  { value: 'GBP', label: 'GBP - British Pound' },
  { value: 'JPY', label: 'JPY - Japanese Yen' },
  { value: 'CAD', label: 'CAD - Canadian Dollar' },
  { value: 'AUD', label: 'AUD - Australian Dollar' },
  { value: 'CHF', label: 'CHF - Swiss Franc' },
  { value: 'CNY', label: 'CNY - Chinese Yuan' },
]

function CreateContractPage() {
  const navigate = useNavigate()
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [clients, setClients] = useState<Array<{ id: string; name: string }>>([])
  const [formData, setFormData] = useState({
    client_id: '',
    contract_number: '',
    start_date: '',
    end_date: '',
    renewal_date: '',
    billing_frequency: '' as PaymentFrequency | '',
    billing_amount: '',
    currency: 'USD',
    payment_status: '' as PaymentStatus | '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  useEffect(() => {
    const fetchClients = async () => {
      try {
        const response = await clientsApi.list({ limit: 100 })
        setClients(response.items.map(c => ({ id: c.id, name: c.name })))
      } catch (error) {
        console.error('Error fetching clients:', error)
      }
    }
    fetchClients()
  }, [])

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.client_id) {
      newErrors.client_id = 'Client is required'
    }

    if (!formData.start_date) {
      newErrors.start_date = 'Start date is required'
    }

    if (formData.end_date && formData.start_date) {
      const start = new Date(formData.start_date)
      const end = new Date(formData.end_date)
      if (end < start) {
        newErrors.end_date = 'End date must be after start date'
      }
    }

    if (formData.renewal_date && formData.start_date) {
      const start = new Date(formData.start_date)
      const renewal = new Date(formData.renewal_date)
      if (renewal < start) {
        newErrors.renewal_date = 'Renewal date must be after start date'
      }
    }

    if (formData.billing_amount) {
      const amount = parseFloat(formData.billing_amount)
      if (isNaN(amount) || amount < 0) {
        newErrors.billing_amount = 'Billing amount must be a valid positive number'
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
      const contractData: any = {
        client_id: formData.client_id,
        contract_number: formData.contract_number.trim() || null,
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        renewal_date: formData.renewal_date || null,
        billing_frequency: (formData.billing_frequency as PaymentFrequency) || null,
        billing_amount: formData.billing_amount ? parseFloat(formData.billing_amount) : null,
        currency: formData.currency || null,
        payment_status: (formData.payment_status as PaymentStatus) || null,
      }

      await contractsApi.create(contractData)
      showSuccess('Contract created successfully')
      navigate({ to: '/contracts' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create contract'
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

  const clientOptions = [
    { value: '', label: 'Select client (required)' },
    ...clients.map(c => ({ value: c.id, label: c.name })),
  ]

  return (
    <AppLayout>
      <div className="max-w-2xl mx-auto">
        <button
          onClick={() => navigate({ to: '/contracts' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to Contracts</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create New Contract</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">Contract Information</h2>

          <Select
            label="Client"
            name="client_id"
            value={formData.client_id}
            onChange={(value) => {
              setFormData({ ...formData, client_id: value as string })
              if (errors.client_id) setErrors({ ...errors, client_id: '' })
            }}
            options={clientOptions}
            error={errors.client_id}
            required
            placeholder="Select client"
          />

          <FormField
            label="Contract Number"
            name="contract_number"
            value={formData.contract_number}
            onChange={(e) => setFormData({ ...formData, contract_number: e.target.value })}
            placeholder="Optional - auto-generated if not provided"
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
            required
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

          <DatePicker
            label="Renewal Date"
            name="renewal_date"
            value={formData.renewal_date}
            onChange={(value) => {
              setFormData({ ...formData, renewal_date: value })
              if (errors.renewal_date) setErrors({ ...errors, renewal_date: '' })
            }}
            error={errors.renewal_date}
          />

          <h2 className="text-lg font-semibold text-safe mb-4 mt-6">Billing Configuration</h2>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <FormField
                label="Billing Amount"
                name="billing_amount"
                type="number"
                step="0.01"
                min="0"
                value={formData.billing_amount}
                onChange={(e) => {
                  setFormData({ ...formData, billing_amount: e.target.value })
                  if (errors.billing_amount) setErrors({ ...errors, billing_amount: '' })
                }}
                error={errors.billing_amount}
                placeholder="0.00"
              />
            </div>
            <div>
              <Select
                label="Currency"
                name="currency"
                value={formData.currency}
                onChange={(value) => setFormData({ ...formData, currency: value as string })}
                options={currencyOptions}
                placeholder="Select currency"
              />
            </div>
          </div>

          <Select
            label="Billing Frequency"
            name="billing_frequency"
            value={formData.billing_frequency}
            onChange={(value) => setFormData({ ...formData, billing_frequency: value as PaymentFrequency })}
            options={billingFrequencyOptions}
            placeholder="Select frequency"
          />

          <Select
            label="Payment Status"
            name="payment_status"
            value={formData.payment_status}
            onChange={(value) => setFormData({ ...formData, payment_status: value as PaymentStatus })}
            options={paymentStatusOptions}
            placeholder="Select status"
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
                'Create Contract'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/contracts' })}
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
