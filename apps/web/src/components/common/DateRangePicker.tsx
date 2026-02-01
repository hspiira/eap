/**
 * DateRangePicker Component
 * shadcn Calendar range mode for selecting a date range (from/to).
 */
"use client"

import * as React from 'react'
import { format } from 'date-fns'
import { ChevronDown } from 'lucide-react'
import type { DateRange } from 'react-day-picker'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Label } from '@/components/ui/label'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

export interface DateRangeValue {
  from: string
  to: string
}

export interface DateRangePickerProps {
  label?: string
  name?: string
  value?: DateRangeValue
  onChange: (value: DateRangeValue) => void
  error?: string
  required?: boolean
  disabled?: boolean
  placeholder?: string
  className?: string
  /** Number of months to display side by side */
  numberOfMonths?: number
}

function toDateRange(value?: DateRangeValue): DateRange | undefined {
  if (!value?.from) return undefined
  return {
    from: new Date(value.from + 'T12:00:00'),
    to: value.to ? new Date(value.to + 'T12:00:00') : undefined,
  }
}

function fromDateRange(range: DateRange | undefined): DateRangeValue {
  if (!range?.from) return { from: '', to: '' }
  const y = range.from.getFullYear()
  const m = String(range.from.getMonth() + 1).padStart(2, '0')
  const d = String(range.from.getDate()).padStart(2, '0')
  const from = `${y}-${m}-${d}`
  if (!range.to) return { from, to: '' }
  const ty = range.to.getFullYear()
  const tm = String(range.to.getMonth() + 1).padStart(2, '0')
  const td = String(range.to.getDate()).padStart(2, '0')
  return { from, to: `${ty}-${tm}-${td}` }
}

export function DateRangePicker({
  label,
  name,
  value,
  onChange,
  error,
  required = false,
  disabled = false,
  placeholder = 'Pick a date range',
  className = '',
  numberOfMonths = 2,
}: DateRangePickerProps) {
  const [open, setOpen] = React.useState(false)
  const range = toDateRange(value)

  const handleSelect = (r: DateRange | undefined) => {
    if (!r?.from) {
      onChange({ from: '', to: '' })
      return
    }
    const next = fromDateRange(r)
    onChange(next)
    if (r.to) setOpen(false)
  }

  const displayText = range?.from
    ? range.to
      ? `${format(range.from, 'LLL dd, y')} - ${format(range.to, 'LLL dd, y')}`
      : format(range.from, 'LLL dd, y')
    : placeholder

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
            id={name}
            variant="outline"
            disabled={disabled}
            className={cn(
              'w-full justify-between font-normal rounded-none',
              !range?.from && 'text-text-muted',
              error && 'border-danger'
            )}
          >
            {displayText}
            <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="z-[110] w-auto overflow-hidden p-0 rounded-none" align="start">
          <Calendar
            mode="range"
            selected={range}
            defaultMonth={range?.from}
            onSelect={handleSelect}
            numberOfMonths={numberOfMonths}
          />
        </PopoverContent>
      </Popover>
      {error && <p className="mt-1 text-sm text-danger">{error}</p>}
    </div>
  )
}
