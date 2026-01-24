/**
 * Create KPI Page
 * Form to create a new KPI with category, measurement unit, and target value
 */

import { createFileRoute, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { AppLayout } from '@/components/layout/AppLayout'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { kpisApi } from '@/api/endpoints/kpis'
import { KPICategory, MeasurementUnit } from '@/types/enums'
import { ArrowLeft } from 'lucide-react'

export const Route = createFileRoute('/kpis/new')({
  component: CreateKPIPage,
})

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

function CreateKPIPage() {
  const navigate = useNavigate()
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

  const validateForm = () => {
    const newErrors: Record<string, string> = {}

    if (!formData.name.trim()) {
      newErrors.name = 'KPI name is required'
    }

    if (!formData.category) {
      newErrors.category = 'Category is required'
    }

    if (!formData.measurement_unit) {
      newErrors.measurement_unit = 'Measurement unit is required'
    }

    if (formData.target_value) {
      const target = parseFloat(formData.target_value)
      if (isNaN(target) || target < 0) {
        newErrors.target_value = 'Target value must be a valid positive number'
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
      const kpiData: any = {
        name: formData.name.trim(),
        description: formData.description.trim() || null,
        category: formData.category as KPICategory,
        measurement_unit: formData.measurement_unit as MeasurementUnit,
        target_value: formData.target_value ? parseFloat(formData.target_value) : null,
      }

      await kpisApi.create(kpiData)
      showSuccess('KPI created successfully')
      navigate({ to: '/kpis' })
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create KPI'
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
          onClick={() => navigate({ to: '/kpis' })}
          className="flex items-center gap-2 text-safe hover:text-natural mb-6 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>Back to KPIs</span>
        </button>

        <h1 className="text-3xl font-bold text-safe mb-6">Create New KPI</h1>

        <form onSubmit={handleSubmit} className="bg-calm border border-[0.5px] border-safe p-6">
          <h2 className="text-lg font-semibold text-safe mb-4">KPI Information</h2>

          <FormField
            label="KPI Name"
            name="name"
            value={formData.name}
            onChange={(e) => {
              setFormData({ ...formData, name: e.target.value })
              if (errors.name) setErrors({ ...errors, name: '' })
            }}
            error={errors.name}
            required
            placeholder="Enter KPI name"
          />

          <FormField
            label="Description"
            name="description"
            type="textarea"
            value={formData.description}
            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
            placeholder="Enter KPI description (optional)"
            rows={4}
          />

          <Select
            label="Category"
            name="category"
            value={formData.category}
            onChange={(value) => {
              setFormData({ ...formData, category: value as KPICategory })
              if (errors.category) setErrors({ ...errors, category: '' })
            }}
            options={categoryOptions}
            error={errors.category}
            required
            placeholder="Select category"
          />

          <Select
            label="Measurement Unit"
            name="measurement_unit"
            value={formData.measurement_unit}
            onChange={(value) => {
              setFormData({ ...formData, measurement_unit: value as MeasurementUnit })
              if (errors.measurement_unit) setErrors({ ...errors, measurement_unit: '' })
            }}
            options={measurementUnitOptions}
            error={errors.measurement_unit}
            required
            placeholder="Select measurement unit"
          />

          <FormField
            label="Target Value"
            name="target_value"
            type="number"
            step="0.01"
            min="0"
            value={formData.target_value}
            onChange={(e) => {
              setFormData({ ...formData, target_value: e.target.value })
              if (errors.target_value) setErrors({ ...errors, target_value: '' })
            }}
            error={errors.target_value}
            placeholder="Enter target value (optional)"
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
                'Create KPI'
              )}
            </button>
            <button
              type="button"
              onClick={() => navigate({ to: '/kpis' })}
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
