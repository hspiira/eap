/**
 * Create KPI Form
 * Used inside CreateModal on kpis list page
 */

import { useState } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { kpisApi } from '@/api/endpoints/kpis'
import { KPICategory, MeasurementUnit } from '@/types/enums'

const categoryOptions = [
  { value: '', label: 'Select category (required)' },
  { value: KPICategory.UTILIZATION, label: 'Utilization' },
  { value: KPICategory.SATISFACTION, label: 'Satisfaction' },
  { value: KPICategory.OUTCOME, label: 'Outcome' },
  { value: KPICategory.OPERATIONAL, label: 'Operational' },
]

const measurementUnitOptions = [
  { value: '', label: 'Select measurement unit (required)' },
  { value: MeasurementUnit.PERCENTAGE, label: 'Percentage (%)' },
  { value: MeasurementUnit.COUNT, label: 'Count' },
  { value: MeasurementUnit.RATE, label: 'Rate' },
  { value: MeasurementUnit.SCORE, label: 'Score' },
  { value: MeasurementUnit.TIME, label: 'Time (minutes)' },
  { value: MeasurementUnit.CURRENCY, label: 'Currency (USD)' },
]

export interface CreateKpiFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateKpiForm({ onSuccess, onCancel, onLoadingChange }: CreateKpiFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '' as KPICategory | '',
    measurement_unit: '' as MeasurementUnit | '',
    target_value: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const setLoadingState = (v: boolean) => { setLoading(v); onLoadingChange?.(v) }

  const validateForm = () => {
    const next: Record<string, string> = {}
    if (!formData.name.trim()) next.name = 'KPI name is required'
    if (!formData.category) next.category = 'Category is required'
    if (!formData.measurement_unit) next.measurement_unit = 'Measurement unit is required'
    if (formData.target_value) {
      const n = parseFloat(formData.target_value)
      if (isNaN(n) || n < 0) next.target_value = 'Target value must be a valid positive number'
    }
    setErrors(next)
    return Object.keys(next).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return
    try {
      setLoadingState(true)
      await kpisApi.create({
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        category: formData.category as KPICategory,
        measurement_unit: formData.measurement_unit as MeasurementUnit,
        target_value: formData.target_value ? parseFloat(formData.target_value) : null,
      })
      showSuccess('KPI created successfully')
      onSuccess()
    } catch (err: any) {
      showError(err.message || 'Failed to create KPI')
      if (err.details) { const m: Record<string, string> = {}; err.details.forEach((d: any) => { if (d.field) m[d.field] = d.message }); setErrors(m) }
    } finally {
      setLoadingState(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormField label="KPI Name" name="name" value={formData.name} onChange={(e) => { setFormData({ ...formData, name: e.target.value }); if (errors.name) setErrors({ ...errors, name: '' }) }} error={errors.name} required placeholder="Enter KPI name" />
      <FormField label="Description" name="description" type="textarea" rows={3} value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} placeholder="Optional" />
      <Select label="Category" name="category" value={formData.category} onChange={(v) => { setFormData({ ...formData, category: v as KPICategory }); if (errors.category) setErrors({ ...errors, category: '' }) }} options={categoryOptions} error={errors.category} required placeholder="Select category" />
      <Select label="Measurement Unit" name="measurement_unit" value={formData.measurement_unit} onChange={(v) => { setFormData({ ...formData, measurement_unit: v as MeasurementUnit }); if (errors.measurement_unit) setErrors({ ...errors, measurement_unit: '' }) }} options={measurementUnitOptions} error={errors.measurement_unit} required placeholder="Select unit" />
      <FormField label="Target Value" name="target_value" type="number" step="0.01" min={0} value={formData.target_value} onChange={(e) => { setFormData({ ...formData, target_value: e.target.value }); if (errors.target_value) setErrors({ ...errors, target_value: '' }) }} error={errors.target_value} placeholder="Optional" />

      <div className="flex gap-3 pt-4">
        <button type="submit" disabled={loading} className="flex-1 px-6 py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50">
          {loading ? <span className="flex items-center justify-center gap-2"><LoadingSpinner size="sm" color="white" />Creating...</span> : 'Create KPI'}
        </button>
        <button type="button" onClick={onCancel} disabled={loading} className="px-6 py-3 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors disabled:opacity-50">Cancel</button>
      </div>
    </form>
  )
}
