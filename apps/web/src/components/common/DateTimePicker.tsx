/**
 * DateTimePicker Component
 * Combines DatePicker + time input for date and time selection.
 */
"use client"

import * as React from 'react'
import { format } from 'date-fns'
import { ChevronDown } from 'lucide-react'

import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Calendar } from '@/components/ui/calendar'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

export interface DateTimeValue {
  date: string
  time: string
}

export interface DateTimePickerProps {
  label?: string
  dateLabel?: string
  timeLabel?: string
  name?: string
  value?: DateTimeValue
  onChange: (value: DateTimeValue) => void
  error?: string
  dateError?: string
  timeError?: string
  required?: boolean
  disabled?: boolean
  datePlaceholder?: string
  className?: string
  min?: string
  max?: string
}

export function DateTimePicker({
  label,
  dateLabel = 'Date',
  timeLabel = 'Time',
  name,
  value = { date: '', time: '' },
  onChange,
  error,
  dateError,
  timeError,
  required = false,
  disabled = false,
  datePlaceholder = 'Select date',
  className = '',
  min,
  max,
}: DateTimePickerProps) {
  const [open, setOpen] = React.useState(false)

  const date = value.date ? new Date(value.date + 'T12:00:00') : undefined
  const minDate = min ? new Date(min + 'T00:00:00') : undefined
  const maxDate = max ? new Date(max + 'T23:59:59') : undefined

  const handleDateSelect = (d: Date | undefined) => {
    if (!d) {
      onChange({ ...value, date: '' })
      return
    }
    const y = d.getFullYear()
    const m = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    onChange({ ...value, date: `${y}-${m}-${day}` })
    setOpen(false)
  }

  const handleTimeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange({ ...value, time: e.target.value })
  }

  const displayDate = date ? format(date, 'PPP') : datePlaceholder

  return (
    <div className={cn('mb-4', className)}>
      {label && (
        <Label className="block text-text text-sm font-medium mb-2">
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </Label>
      )}
      <div className="flex gap-2 flex-wrap">
        <div className="flex-1 min-w-[140px]">
          <Label htmlFor={name ? `${name}-date` : undefined} className="block text-text text-sm font-medium mb-1">
            {dateLabel}
            {required && <span className="text-danger ml-1">*</span>}
          </Label>
          <Popover open={open} onOpenChange={setOpen} modal={false}>
            <PopoverTrigger asChild>
              <Button
                id={name ? `${name}-date` : undefined}
                variant="outline"
                disabled={disabled}
                className={cn(
                  'w-full justify-between font-normal rounded-none',
                  !date && 'text-text-muted',
                  (error || dateError) && 'border-danger'
                )}
              >
                {displayDate}
                <ChevronDown className="ml-2 h-4 w-4 opacity-50" />
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
                onSelect={handleDateSelect}
              />
            </PopoverContent>
          </Popover>
          {(error || dateError) && <p className="mt-1 text-sm text-danger">{dateError || error}</p>}
        </div>
        <div className="w-32 shrink-0">
          <Label htmlFor={name ? `${name}-time` : undefined} className="block text-text text-sm font-medium mb-1">
            {timeLabel}
            {required && <span className="text-danger ml-1">*</span>}
          </Label>
          <Input
            type="time"
            id={name ? `${name}-time` : undefined}
            value={value.time}
            onChange={handleTimeChange}
            disabled={disabled}
            step="1"
            className={cn('rounded-none', (error || timeError) && 'border-danger')}
          />
          {(error || timeError) && <p className="mt-1 text-sm text-danger">{timeError || error}</p>}
        </div>
      </div>
    </div>
  )
}
