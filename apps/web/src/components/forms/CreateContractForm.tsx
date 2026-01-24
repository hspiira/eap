/**
 * Create Contract Form
 * Used inside CreateModal on contracts list page
 */

import { useState, useEffect } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { DatePicker } from '@/components/common/DatePicker'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { contractsApi } from '@/api/endpoints/contracts'
import { clientsApi } from '@/api/endpoints/clients'
import type { PaymentFrequency, PaymentStatus } from '@/types/enums'

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
  { value: 'USD', label: 'USD' },
  { value: 'EUR', label: 'EUR' },
  { value: 'GBP', label: 'GBP' },
  { value: 'JPY', label: 'JPY' },
  { value: 'CAD', label: 'CAD' },
  { value: 'AUD', label: 'AUD' },
  { value: 'CHF', label: 'CHF' },
  { value: 'CNY', label: 'CNY' },
]

export interface CreateContractFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateContractForm({ onSuccess, onCancel, onLoadingChange }: CreateContractFormProps) {
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
        const res = await clientsApi.list({ limit: 100 })
        setClients(res.items.map((c) => ({ id: c.id, name: c.name })))
      } catch (err) {
        console.error('Error fetching clients:', err)
      }
    }
    fetchClients()
  }, [])

  const setLoadingState = (v: boolean) => {
    setLoading(v)
    onLoadingChange?.(v)
  }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.client_id) next.client_id = 'Client is required'
    if (!formData.start_date) next.start_date = 'Start date is required'
    if (formData.end_date && formData.start_date) {
      if (new Date(formData.end_date) < new Date(formData.start_date)) next.end_date = 'End date must be after start date'
    }
    if (formData.renewal_date && formData.start_date) {
      if (new Date(formData.renewal_date) < new Date(formData.start_date)) next.renewal_date = 'Renewal date must be after start date'
    }
    if (formData.billing_amount) {
      const n = parseFloat(formData.billing_amount)
      if (isNaN(n) || n < 0) next.billing_amount = 'Billing amount must be a valid positive number'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      setLoadingState(true)
      await contractsApi.create({
        client_id: formData.client_id,
        contract_number: formData.contract_number.trim() || null,
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        renewal_date: formData.renewal_date || null,
        billing_frequency: (formData.billing_frequency as PaymentFrequency) || null,
        billing_amount: formData.billing_amount ? parseFloat(formData.billing_amount) : null,
        currency: formData.currency || null,
        payment_status: (formData.payment_status as PaymentStatus) || null,
      })
      showSuccess('Contract created successfully')
      onSuccess()
    } catch (err: any) {
      showError(err.message || 'Failed to create contract')
      if (err.details) {
        const map: Record<string, string> = {}
        err.details.forEach((d: any) => { if (d.field) map[d.field] = d.message })
        setErrors(map)
      }
    } finally {
      setLoadingState(false)
    }
  }

  const clientOptions = [{ value: '', label: 'Select client (required)' }, ...clients.map((c) => ({ value: c.id, label: c.name }))]

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-sm font-semibold text-safe">Contract Information</h3>
      <Select
        label="Client"
        name="client_id"
        value={formData.client_id}
        onChange={(v) => { setFormData({ ...formData, client_id: v as string }); if (errors.client_id) setErrors({ ...errors, client_id: '' }) }}
        options={clientOptions}
        error={errors.client_id}
        required
        placeholder="Select client"
      />
      <FormField label="Contract Number" name="contract_number" value={formData.contract_number} onChange={(e) => setFormData({ ...formData, contract_number: e.target.value })} placeholder="Optional" />

      <h3 className="text-sm font-semibold text-safe mt-4">Dates</h3>
      <DatePicker label="Start Date" name="start_date" value={formData.start_date} onChange={(v) => { setFormData({ ...formData, start_date: v }); if (errors.start_date) setErrors({ ...errors, start_date: '' }) }} error={errors.start_date} required />
      <DatePicker label="End Date" name="end_date" value={formData.end_date} onChange={(v) => { setFormData({ ...formData, end_date: v }); if (errors.end_date) setErrors({ ...errors, end_date: '' }) }} error={errors.end_date} />
      <DatePicker label="Renewal Date" name="renewal_date" value={formData.renewal_date} onChange={(v) => { setFormData({ ...formData, renewal_date: v }); if (errors.renewal_date) setErrors({ ...errors, renewal_date: '' }) }} error={errors.renewal_date} />

      <h3 className="text-sm font-semibold text-safe mt-4">Billing</h3>
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Billing Amount"
          name="billing_amount"
          type="number"
          step="0.01"
          min="0"
          value={formData.billing_amount}
          onChange={(e) => { setFormData({ ...formData, billing_amount: e.target.value }); if (errors.billing_amount) setErrors({ ...errors, billing_amount: '' }) }}
          error={errors.billing_amount}
          placeholder="0.00"
        />
        <Select label="Currency" name="currency" value={formData.currency} onChange={(v) => setFormData({ ...formData, currency: v as string })} options={currencyOptions} placeholder="Currency" />
      </div>
      <Select label="Billing Frequency" name="billing_frequency" value={formData.billing_frequency} onChange={(v) => setFormData({ ...formData, billing_frequency: v as PaymentFrequency })} options={billingFrequencyOptions} placeholder="Optional" />
      <Select label="Payment Status" name="payment_status" value={formData.payment_status} onChange={(v) => setFormData({ ...formData, payment_status: v as PaymentStatus })} options={paymentStatusOptions} placeholder="Optional" />

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create Contract'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
