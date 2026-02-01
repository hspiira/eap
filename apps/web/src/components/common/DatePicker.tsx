/**
 * DatePicker Component
 * shadcn Calendar + Popover. Uses modal={false} for better compatibility.
 */
"use client"

import * as React from 'react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Label } from '@/components/ui/label'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

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
  placeholder = 'Select date',
  className = '',
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false)

  const date = value ? new Date(value + 'T12:00:00') : undefined
  const minDate = min ? new Date(min + 'T00:00:00') : undefined
  const maxDate = max ? new Date(max + 'T23:59:59') : undefined

  const handleSelect = (d: Date | undefined) => {
    if (!d) {
      onChange('')
      return
    }
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    onChange(`${y}-${m}-${day}`)
    setOpen(false)
  }

  return (
    <div className={cn('mb-4', className)}>
      {label && (
        <Label htmlFor={name} className="block text-text text-sm font-medium mb-2">
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </Label>
      )}
      <Popover open={open} onOpenChange={setOpen} modal={false}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            id={name}
            variant="outline"
            disabled={disabled}
            className={cn(
              'w-full justify-start font-normal rounded-none',
              !date && 'text-text-muted',
              error && 'border-danger'
            )}
          >
            {date ? date.toLocaleDateString() : placeholder}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="z-[110] w-auto overflow-hidden p-0 rounded-none" align="start">
          <Calendar
            mode="single"
            selected={date}
            defaultMonth={date}
            captionLayout="dropdown"
            startMonth={minDate}
            endMonth={maxDate}
            disabled={(d) => {
              if (minDate && d < minDate) return true
              if (maxDate && d > maxDate) return true
              return false
            }}
            onSelect={handleSelect}
          />
        </PopoverContent>
      </Popover>
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  )
}
