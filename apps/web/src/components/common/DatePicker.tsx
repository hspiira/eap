/**
 * DatePicker Component
 * Reusable date input component
 */

import { Calendar } from 'lucide-react'

export interface DatePickerProps {
  label?: string
  name: string
  value: string
  onChange: (value: string) => void
  error?: string
  required?: boolean
  disabled?: boolean
  min?: string
  max?: string
  placeholder?: string
  className?: string
}

export function DatePicker({
  label,
  name,
  value,
  onChange,
  error,
  required = false,
  disabled = false,
  min,
  max,
  placeholder,
  className = '',
}: DatePickerProps) {
  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label
          htmlFor={name}
          className="block text-text text-sm font-medium mb-2"
        >
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <input
          type="date"
          id={name}
          name={name}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          min={min}
          max={max}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          className={`w-full px-4 py-2 bg-surface border-[0.5px] ${
            error ? 'border-danger' : 'border-border'
          } rounded-none focus:outline-none focus:border-border-focus ${
            disabled ? 'opacity-50 cursor-not-allowed' : ''
          }`}
        />
        <Calendar
          size={18}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 text-text-muted pointer-events-none"
        />
      </div>
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  )
}
