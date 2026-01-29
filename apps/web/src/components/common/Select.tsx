/**
 * Select Component
 * Reusable select dropdown with search and multi-select support
 */

import { useState, useRef, useEffect } from 'react'
import { ChevronDown, X, Check } from 'lucide-react'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps {
  label?: string
  name: string
  value: string | string[]
  onChange: (value: string | string[]) => void
  options: SelectOption[]
  multiple?: boolean
  searchable?: boolean
  placeholder?: string
  error?: string
  required?: boolean
  disabled?: boolean
  className?: string
  /** Tighter spacing (e.g. in modals) */
  compact?: boolean
}

export function Select({
  label,
  name,
  value,
  onChange,
  options,
  multiple = false,
  searchable = false,
  placeholder = 'Select an option...',
  error,
  required = false,
  disabled = false,
  className = '',
  compact = false,
}: SelectProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchTerm, setSearchTerm] = useState('')
  const selectRef = useRef<HTMLDivElement>(null)
  const searchInputRef = useRef<HTMLInputElement>(null)

  const selectedValues = Array.isArray(value) ? value : value ? [value] : []

  // Filter options based on search term
  const filteredOptions = searchable
    ? options.filter((option) =>
        option.label.toLowerCase().includes(searchTerm.toLowerCase())
      )
    : options

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (selectRef.current && !selectRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setSearchTerm('')
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      // Focus search input when opening
      if (searchable && searchInputRef.current) {
        setTimeout(() => searchInputRef.current?.focus(), 0)
      }
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen, searchable])

  const handleToggle = () => {
    if (!disabled) {
      setIsOpen(!isOpen)
    }
  }

  const handleSelect = (optionValue: string) => {
    if (multiple) {
      const newValues = selectedValues.includes(optionValue)
        ? selectedValues.filter((v) => v !== optionValue)
        : [...selectedValues, optionValue]
      onChange(newValues)
    } else {
      onChange(optionValue)
      setIsOpen(false)
      setSearchTerm('')
    }
  }

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation()
    onChange(multiple ? [] : '')
  }

  const getDisplayValue = () => {
    if (multiple) {
      if (selectedValues.length === 0) {
        return placeholder
      }
      if (selectedValues.length === 1) {
        const option = options.find((opt) => opt.value === selectedValues[0])
        return option?.label || placeholder
      }
      return `${selectedValues.length} selected`
    }
    const option = options.find((opt) => opt.value === value)
    return option?.label || placeholder
  }

  const isSelected = (optionValue: string) => {
    return selectedValues.includes(optionValue)
  }

  const space = compact ? 'mb-2' : 'mb-4'
  const labelSpace = compact ? 'mb-1' : 'mb-2'

  return (
    <div className={`${space} ${className}`}>
      {label && (
        <label
          htmlFor={name}
          className={`block text-safe text-sm font-medium ${labelSpace}`}
        >
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
      )}
      <div ref={selectRef} className="relative">
        <button
          type="button"
          onClick={handleToggle}
          disabled={disabled}
          className={`w-full px-4 py-2 bg-white border-[0.5px] ${
            error ? 'border-danger' : 'border-safe/30'
          } rounded-none focus:outline-none focus:border-natural flex items-center justify-between ${
            disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'
          }`}
        >
          <span className={`text-left flex-1 ${!value || (Array.isArray(value) && value.length === 0) ? 'text-safe-light' : 'text-safe'}`}>
            {getDisplayValue()}
          </span>
          <div className="flex items-center gap-2">
            {value && (Array.isArray(value) ? value.length > 0 : true) && !disabled && (
              <button
                type="button"
                onClick={handleClear}
                className="p-1 hover:bg-safe-light/20 rounded-none transition-colors"
                aria-label="Clear selection"
              >
                <X size={16} className="text-safe" />
              </button>
            )}
            <ChevronDown
              size={18}
              className={`text-safe transition-transform ${isOpen ? 'rotate-180' : ''}`}
            />
          </div>
        </button>

        {isOpen && (
          <div className="absolute z-50 w-full mt-1 bg-white border border-[0.5px] border-safe/30 shadow-lg max-h-60 overflow-auto">
            {searchable && (
              <div className="p-2">
                <input
                  ref={searchInputRef}
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search..."
                  className="w-full px-3 py-1.5 bg-white border border-[0.5px] border-safe/30 text-safe rounded-none focus:outline-none focus:border-natural"
                />
              </div>
            )}
            <div className="py-1">
              {filteredOptions.length === 0 ? (
                <div className="px-4 py-2 text-sm text-safe-light">No options found</div>
              ) : (
                filteredOptions.map((option) => {
                  const selected = isSelected(option.value)
                  return (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => !option.disabled && handleSelect(option.value)}
                      disabled={option.disabled}
                      className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 hover:bg-gray-100 transition-colors ${
                        selected ? 'bg-natural/10 text-natural' : 'text-safe'
                      } ${option.disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                    >
                      {multiple && (
                        <div
                          className={`w-4 h-4 border border-[0.5px] border-safe/30 flex items-center justify-center ${
                            selected ? 'bg-natural border-natural-dark' : 'bg-white'
                          }`}
                        >
                          {selected && <Check size={12} className="text-white" />}
                        </div>
                      )}
                      <span className="flex-1">{option.label}</span>
                    </button>
                  )
                })
              )}
            </div>
          </div>
        )}
      </div>
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  )
}
