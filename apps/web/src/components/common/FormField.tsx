/**
 * Form Field Component
 * Reusable form field with label, input, and error display
 * Supports both controlled and React Hook Form integration
 */

import { useFormContext, Controller } from 'react-hook-form'
import { getFieldError } from '@/utils/validators'

interface FormFieldProps {
  label: string
  name: string
  type?: 'text' | 'email' | 'password' | 'number' | 'tel' | 'url' | 'textarea'
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void
  error?: string
  required?: boolean
  placeholder?: string
  autoComplete?: string
  disabled?: boolean
  min?: number
  max?: number
  rows?: number
  className?: string
  /** Tighter spacing (e.g. in modals) */
  compact?: boolean
  // React Hook Form integration
  useFormContext?: boolean
}

export function FormField({
  label,
  name,
  type = 'text',
  value: controlledValue,
  onChange: controlledOnChange,
  error: externalError,
  required = false,
  placeholder,
  autoComplete,
  disabled = false,
  min,
  max,
  rows = 4,
  className = '',
  compact = false,
  useFormContext: useForm = false,
}: FormFieldProps) {
  const formContext = useForm ? useFormContext() : null
  const formError = formContext ? getFieldError(formContext.formState.errors, name) : null
  const error = externalError || formError
  const space = compact ? 'mb-2' : 'mb-4'
  const labelSpace = compact ? 'mb-1' : 'mb-2'

  // If using React Hook Form, use Controller
  if (useForm && formContext) {
    return (
      <div className={`${space} ${className}`}>
        <label
          htmlFor={name}
          className={`block text-safe text-sm font-medium ${labelSpace}`}
        >
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
        <Controller
          name={name}
          control={formContext.control}
          render={({ field }) => {
            if (type === 'textarea') {
              return (
                <textarea
                  {...field}
                  id={name}
                  rows={rows}
                  placeholder={placeholder}
                  disabled={disabled}
                  required={required}
                  className={`w-full px-4 py-2 bg-white border-[0.5px] ${
                    error ? 'border-danger' : 'border-safe/30'
                  } rounded-none focus:outline-none focus:border-natural ${
                    disabled ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                />
              )
            }
            return (
              <input
                {...field}
                type={type}
                id={name}
                placeholder={placeholder}
                autoComplete={autoComplete}
                disabled={disabled}
                required={required}
                min={min}
                max={max}
                className={`w-full px-4 py-2 bg-white border-[0.5px] ${
                  error ? 'border-danger' : 'border-safe/30'
                } rounded-none focus:outline-none focus:border-natural ${
                  disabled ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              />
            )
          }}
        />
        {error && <p className="mt-1 text-sm text-danger">{error}</p>}
      </div>
    )
  }

  // Controlled component (non-React Hook Form)
  if (type === 'textarea') {
    return (
      <div className={`${space} ${className}`}>
        <label
          htmlFor={name}
          className={`block text-safe text-sm font-medium ${labelSpace}`}
        >
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
        <textarea
          id={name}
          name={name}
          value={controlledValue || ''}
          onChange={controlledOnChange as any}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          rows={rows}
          className={`w-full px-4 py-2 bg-white border-[0.5px] ${
            error ? 'border-danger' : 'border-safe/30'
          } rounded-none focus:outline-none focus:border-natural ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        />
        {error && <p className="mt-1 text-sm text-danger">{error}</p>}
      </div>
    )
  }

  return (
    <div className={`${space} ${className}`}>
      <label
        htmlFor={name}
        className={`block text-safe text-sm font-medium ${labelSpace}`}
      >
        {label}
        {required && <span className="text-danger ml-1">*</span>}
      </label>
      <input
        type={type}
        id={name}
        name={name}
        value={controlledValue || ''}
        onChange={controlledOnChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required={required}
        disabled={disabled}
        min={min}
        max={max}
        className={`w-full px-4 py-2 bg-white border-[0.5px] ${
          error ? 'border-danger' : 'border-safe/30'
        } rounded-none focus:outline-none focus:border-natural ${
          disabled ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      />
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  )
}
