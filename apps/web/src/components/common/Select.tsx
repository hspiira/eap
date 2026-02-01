/**
 * Select Component
 * Uses shadcn Select (Radix) or Popover+Command (searchable/multi-select) with our API.
 * Popover+Command when searchable=true, options.length > 10, or multiple=true.
 */

"use client"

const EMPTY_VALUE = '__none__'
const SEARCHABLE_THRESHOLD = 10

import { useState } from 'react'
import { Check, ChevronDown } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import {
  Select as ShadcnSelect,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'

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
  const [open, setOpen] = useState(false)
  const selectedValues: string[] = Array.isArray(value)
    ? value.filter((v) => v != null)
    : value != null && value !== ''
      ? [value]
      : []
  const selectedValue = multiple ? selectedValues[0] ?? '' : selectedValues[0] ?? ''
  const hasEmptyOption = options.some((o) => o.value === '')
  const usePopover =
    searchable || options.length > SEARCHABLE_THRESHOLD || multiple

  const normalizedOptions = options.map((o) => ({
    ...o,
    value: o.value === '' ? EMPTY_VALUE : o.value,
  }))

  const selectValue =
    selectedValue === '' && hasEmptyOption ? EMPTY_VALUE : selectedValue || undefined
  const selectValuesSet = new Set(
    selectedValues.map((v) => (v === '' && hasEmptyOption ? EMPTY_VALUE : v))
  )

  const handleValueChange = (val: string) => {
    const out = val === EMPTY_VALUE ? '' : val
    if (multiple) {
      if (val === EMPTY_VALUE) {
        onChange([])
        setOpen(false)
        return
      }
      const next = selectValuesSet.has(val)
        ? selectedValues.filter((v) => (v === '' ? EMPTY_VALUE : v) !== val)
        : [...selectedValues, out]
      onChange(next)
    } else {
      onChange(out)
      setOpen(false)
    }
  }

  const selectedLabel = multiple
    ? selectedValues.length === 0
      ? placeholder
      : selectedValues.length <= 2
        ? selectedValues
            .map(
              (v) =>
                normalizedOptions.find((o) =>
                  o.value === (v === '' && hasEmptyOption ? EMPTY_VALUE : v)
                )?.label ?? v
            )
            .join(', ')
        : `${selectedValues.length} items selected`
    : normalizedOptions.find((o) => o.value === selectValue)?.label ?? placeholder

  const space = compact ? 'mb-2' : 'mb-4'
  const labelSpace = compact ? 'mb-1' : 'mb-2'

  const triggerClassName = cn(
    'w-full justify-between font-normal rounded-none',
    (multiple ? selectedValues.length === 0 : !selectedValue) && 'text-text-muted',
    error && 'border-danger'
  )

  if (usePopover) {
    return (
      <div className={cn(space, className)}>
        {label && (
          <Label htmlFor={name} className={cn('block text-text text-sm font-medium', labelSpace)}>
            {label}
            {required && <span className="text-danger ml-1">*</span>}
          </Label>
        )}
        <Popover open={open} onOpenChange={setOpen} modal={false}>
          <PopoverTrigger asChild>
            <Button
              id={name}
              variant="outline"
              disabled={disabled}
              className={triggerClassName}
            >
              {selectedLabel}
              <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0 z-[110]" align="start">
            <Command>
              <CommandInput placeholder="Search..." className="rounded-none border-0" />
              <CommandList>
                <CommandEmpty>No results found.</CommandEmpty>
                <CommandGroup>
                  {normalizedOptions.map((option) => {
                    const isSelected = multiple
                      ? selectValuesSet.has(option.value)
                      : selectValue === option.value
                    return (
                      <CommandItem
                        key={option.value}
                        value={option.label}
                        disabled={option.disabled}
                        onSelect={() =>
                          !option.disabled && handleValueChange(option.value)
                        }
                        className="rounded-none"
                      >
                        <Check
                          className={cn(
                            'mr-2 h-4 w-4 flex-shrink-0',
                            isSelected ? 'opacity-100' : 'opacity-0'
                          )}
                        />
                        {option.label}
                      </CommandItem>
                    )
                  })}
                </CommandGroup>
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
        {error && <p className="mt-1 text-sm text-danger">{error}</p>}
      </div>
    )
  }

  return (
    <div className={cn(space, className)}>
      {label && (
        <Label htmlFor={name} className={cn('block text-text text-sm font-medium', labelSpace)}>
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </Label>
      )}
      <ShadcnSelect
        value={selectValue}
        onValueChange={handleValueChange}
        disabled={disabled}
      >
        <SelectTrigger
          id={name}
          className={cn('rounded-none', error && 'border-danger', !selectedValue && 'text-text-muted')}
        >
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent className="z-[110]">
          {normalizedOptions.map((option) => (
            <SelectItem
              key={option.value}
              value={option.value}
              disabled={option.disabled}
              className="rounded-none"
            >
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </ShadcnSelect>
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  )
}
