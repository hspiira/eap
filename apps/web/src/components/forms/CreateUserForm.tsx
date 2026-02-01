/**
 * Create User Form
 * Used inside CreateModal on users list page
 */

import { useState } from 'react'
import { FormField } from '@/components/common/FormField'
import { Select } from '@/components/common/Select'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'
import { useToast } from '@/contexts/ToastContext'
import { usersApi } from '@/api/endpoints/users'

const languageOptions = [
  { value: '', label: 'Select language (optional)' },
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'it', label: 'Italian' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ko', label: 'Korean' },
]

const timezoneOptions = [
  { value: '', label: 'Select timezone (optional)' },
  { value: 'UTC', label: 'UTC' },
  { value: 'America/New_York', label: 'Eastern Time (ET)' },
  { value: 'America/Chicago', label: 'Central Time (CT)' },
  { value: 'America/Denver', label: 'Mountain Time (MT)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT)' },
  { value: 'Europe/London', label: 'London (GMT)' },
  { value: 'Europe/Paris', label: 'Paris (CET)' },
  { value: 'Asia/Tokyo', label: 'Tokyo (JST)' },
  { value: 'Asia/Shanghai', label: 'Shanghai (CST)' },
]

export interface CreateUserFormProps {
  onSuccess: () => void
  onCancel: () => void
  onLoadingChange?: (loading: boolean) => void
}

export function CreateUserForm({ onSuccess, onCancel, onLoadingChange }: CreateUserFormProps) {
  const { showSuccess, showError } = useToast()
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    preferred_language: '',
    timezone: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})

  const setLoadingState = (value: boolean) => {
    setLoading(value)
    onLoadingChange?.(value)
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email address'
    }
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!validateForm()) return

    try {
      setLoadingState(true)
      await usersApi.create({
        email: formData.email.trim(),
        password: formData.password,
        preferred_language: formData.preferred_language || undefined,
        timezone: formData.timezone || undefined,
      })
      showSuccess('User created successfully')
      onSuccess()
    } catch (error: any) {
      const errorMessage = error.message || 'Failed to create user'
      showError(errorMessage)
      if (error.details) {
        const fieldErrors: Record<string, string> = {}
        error.details.forEach((detail: any) => {
          if (detail.field) fieldErrors[detail.field] = detail.message
        })
        setErrors(fieldErrors)
      }
    } finally {
      setLoadingState(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <FormField
        label="Email"
        name="email"
        type="email"
        value={formData.email}
        onChange={(e) => {
          setFormData({ ...formData, email: e.target.value })
          if (errors.email) setErrors({ ...errors, email: '' })
        }}
        error={errors.email}
        required
        placeholder="user@example.com"
        autoComplete="email"
      />
      <FormField
        label="Password"
        name="password"
        type="password"
        value={formData.password}
        onChange={(e) => {
          setFormData({ ...formData, password: e.target.value })
          if (errors.password) setErrors({ ...errors, password: '' })
        }}
        error={errors.password}
        required
        placeholder="Enter password"
        autoComplete="new-password"
      />
      <Select
        label="Preferred Language"
        name="preferred_language"
        value={formData.preferred_language}
        onChange={(value) => setFormData({ ...formData, preferred_language: value as string })}
        options={languageOptions}
        placeholder="Select language (optional)"
      />
      <Select
        label="Timezone"
        name="timezone"
        value={formData.timezone}
        onChange={(value) => setFormData({ ...formData, timezone: value as string })}
        options={timezoneOptions}
        placeholder="Select timezone (optional)"
      />
      <div className="flex gap-3 pt-4">
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
            'Create User'
          )}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="px-6 py-3 bg-neutral hover:bg-neutral-dark text-white rounded-none transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  )
}
