/**
 * Window control for the analytics section. It scopes every chart below it,
 * so it lives once above them rather than inside any one card.
 */

import { useState } from "react"

import { CalendarRange, Check } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import type { DashboardRange, RangePreset } from "@/lib/dashboard"
import { cn } from "@/lib/utils"

const PRESETS: ReadonlyArray<{ value: RangePreset; label: string }> = [
  { value: "this_week", label: "Week" },
  { value: "this_month", label: "Month" },
  { value: "last_30d", label: "30d" },
  { value: "last_90d", label: "90d" },
  { value: "last_180d", label: "6m" },
  { value: "this_year", label: "This year" },
  { value: "all_time", label: "All time" },
]

interface RangeFilterProps {
  value: DashboardRange
  onChange: (range: DashboardRange) => void
}

interface RangeFilterOwnProps extends RangeFilterProps {
  /** Years with at least one session, newest first, as the API reports them. */
  years: ReadonlyArray<number>
}

export function RangeFilter({ value, onChange, years }: RangeFilterOwnProps) {
  return (
    <div className="flex flex-wrap items-center gap-1 rounded-md border border-border p-0.5">
      {PRESETS.map((preset) => (
        <PresetButton
          key={preset.value}
          label={preset.label}
          active={value.preset === preset.value}
          onSelect={() => onChange({ preset: preset.value })}
        />
      ))}
      <YearPicker value={value} onChange={onChange} years={years} />
      <CustomRangePopover value={value} onChange={onChange} />
    </div>
  )
}

/**
 * Offers only years the tenant actually delivered in, so the list never
 * promises a year with nothing behind it. Absent entirely until there is at
 * least one, which spares a new tenant a control that can only disappoint.
 */
function YearPicker({ value, onChange, years }: RangeFilterOwnProps) {
  if (years.length === 0) return null
  const active = value.preset === "year"
  return (
    <Select
      value={active && value.year ? String(value.year) : ""}
      onValueChange={(next) => onChange({ preset: "year", year: Number(next) })}
    >
      <SelectTrigger
        aria-label="Year"
        className={cn(
          "h-7 w-auto gap-1 border-0 px-2 text-xs font-medium shadow-none",
          active ? "bg-primary/10 text-primary" : "text-fg-muted",
        )}
      >
        <SelectValue placeholder="Year" />
      </SelectTrigger>
      <SelectContent align="end">
        {years.map((year) => (
          <SelectItem key={year} value={String(year)}>
            {year}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

function PresetButton({
  label,
  active,
  onSelect,
}: {
  label: string
  active: boolean
  onSelect: () => void
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      aria-pressed={active}
      onClick={onSelect}
      className={cn(
        "h-7 px-2 text-xs font-medium",
        active ? "bg-primary/10 text-primary hover:bg-primary/10" : "text-fg-muted",
      )}
    >
      {label}
    </Button>
  )
}

function CustomRangePopover({ value, onChange }: RangeFilterProps) {
  const [open, setOpen] = useState(false)
  const [start, setStart] = useState(value.start ?? "")
  const [end, setEnd] = useState(value.end ?? "")
  const active = value.preset === "custom"

  const apply = () => {
    if (!start) return
    onChange({ preset: "custom", start, end: end || undefined })
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-pressed={active}
          className={cn(
            "h-7 gap-1 px-2 text-xs font-medium",
            active ? "bg-primary/10 text-primary hover:bg-primary/10" : "text-fg-muted",
          )}
        >
          <CalendarRange className="size-3.5" />
          {active ? formatCustomLabel(value) : "Custom"}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="grid w-64 gap-3">
        <div className="grid gap-1.5">
          <Label htmlFor="range-start" className="text-xs">
            From
          </Label>
          <Input
            id="range-start"
            type="date"
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </div>
        <div className="grid gap-1.5">
          <Label htmlFor="range-end" className="text-xs">
            To
          </Label>
          <Input id="range-end" type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
        </div>
        <Button type="button" size="sm" disabled={!start} onClick={apply}>
          <Check className="size-3.5" />
          Apply
        </Button>
      </PopoverContent>
    </Popover>
  )
}

function formatCustomLabel(range: DashboardRange): string {
  if (!range.start) return "Custom"
  return range.end ? `${range.start} to ${range.end}` : `Since ${range.start}`
}
