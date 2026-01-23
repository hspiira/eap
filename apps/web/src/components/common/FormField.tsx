/**
 * Form Field Component
 * Reusable form field with label, input, and error display
 */

interface FormFieldProps {
  label: string
  name: string
  type?: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  error?: string
  required?: boolean
  placeholder?: string
  autoComplete?: string
}

export function FormField({
  label,
  name,
  type = 'text',
  value,
  onChange,
  error,
  required = false,
  placeholder,
  autoComplete,
}: FormFieldProps) {
  return (
    <div className="mb-4">
      <label
        htmlFor={name}
        className="block text-safe text-sm font-medium mb-2"
      >
        {label}
        {required && <span className="text-nurturing ml-1">*</span>}
      </label>
      <input
        type={type}
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        autoComplete={autoComplete}
        required={required}
        className={`w-full px-4 py-2 bg-calm border-[0.5px] ${
          error ? 'border-nurturing' : 'border-safe'
        } rounded-none focus:outline-none focus:border-natural`}
      />
      {error && (
        <p className="mt-1 text-sm text-nurturing">{error}</p>
      )}
    </div>
  )
}
