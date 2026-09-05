import { useState } from "react"

import { CalendarDays } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { formatDay } from "@/lib/format"

interface DatePickerProps {
  value?: string | null
  onChange: (value: string) => void
  placeholder?: string
  id?: string
  "aria-label"?: string
}

function parseDayKey(value?: string | null) {
  if (!value) return undefined
  const [year, month, day] = value.slice(0, 10).split("-").map(Number)
  if (!year || !month || !day) return undefined
  return new Date(year, month - 1, day)
}

function toDayKey(value: Date) {
  const year = value.getFullYear()
  const month = String(value.getMonth() + 1).padStart(2, "0")
  const day = String(value.getDate()).padStart(2, "0")
  return `${year}-${month}-${day}`
}

export function DatePicker({
  value,
  onChange,
  placeholder = "Select date",
  id,
  "aria-label": ariaLabel,
}: DatePickerProps) {
  const [open, setOpen] = useState(false)
  const selected = parseDayKey(value)

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          id={id}
          type="button"
          variant="outline"
          role="combobox"
          aria-expanded={open}
          aria-label={ariaLabel}
          className="h-9 w-full justify-start gap-2 rounded-none px-3 font-normal"
        >
          <CalendarDays className="size-3.5 shrink-0 text-fg-muted" aria-hidden />
          <span className={value ? "text-fg" : "text-fg-muted"}>
            {value ? formatDay(value) : placeholder}
          </span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[18rem] max-w-[calc(100vw-2rem)] rounded-none p-0" align="start">
        <Calendar
          mode="single"
          className="w-full [--cell-size:2.5rem]"
          selected={selected}
          onSelect={(date) => {
            onChange(date ? toDayKey(date) : "")
            setOpen(false)
          }}
          initialFocus
        />
        {value ? (
          <div className="border-t border-fg/10 p-2">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="h-7 w-full rounded-none text-xs"
              onClick={() => {
                onChange("")
                setOpen(false)
              }}
            >
              Clear date
            </Button>
          </div>
        ) : null}
      </PopoverContent>
    </Popover>
  )
}
