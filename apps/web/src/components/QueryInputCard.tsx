import { useState } from "react"

import { ChevronDown, Mic, Plus, Send, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
} from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

const MODES = ["Search", "Ask"] as const
type Mode = (typeof MODES)[number]

interface QueryInputCardProps {
  /** Initial query text, e.g. for the gallery preview. */
  initialQuery?: string
  /** Optional submit handler — receives the trimmed query. */
  onSubmit?: (query: string) => void
  className?: string
}

const DEFAULT_QUERY =
  "Show me clients with overdue contracts in the last 30 days, sorted by tier."

export function QueryInputCard({
  initialQuery = DEFAULT_QUERY,
  onSubmit,
  className,
}: QueryInputCardProps = {}) {
  const [mode, setMode] = useState<Mode>("Search")
  const [query, setQuery] = useState(initialQuery)

  return (
    <div className={cn("grid w-full gap-3", className)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <ModeToggle value={mode} onChange={setMode} />
        <FilterChips />
      </div>

      <Card className="rounded-md">
        <CardContent className="p-3">
          <label htmlFor="query-input" className="sr-only">
            Query
          </label>
          <Textarea
            id="query-input"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
            className="min-h-16 resize-none border-0 bg-transparent text-sm leading-relaxed text-fg shadow-none outline-none placeholder:text-fg-subtle focus-visible:ring-0"
            placeholder="Ask anything about your tenant — clients, sessions, incidents, contracts."
          />
          <div className="mt-3 flex items-center justify-between border-t border-border-subtle pt-3">
            <Button variant="ghost" size="sm" className="gap-1.5 px-2">
              <Plus className="size-3.5" />
              <span className="font-mono text-xs tabular-nums">4.10</span>
              <ChevronDown className="size-3" />
            </Button>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="icon" aria-label="Voice input">
                <Mic className="size-4" />
              </Button>
              <Button
                size="icon"
                aria-label="Submit query"
                onClick={() => onSubmit?.(query.trim())}
                disabled={query.trim().length === 0}
              >
                <Send className="size-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function ModeToggle({
  value,
  onChange,
}: {
  value: Mode
  onChange: (m: Mode) => void
}) {
  return (
    <div
      role="radiogroup"
      aria-label="Query mode"
      className="inline-flex rounded-sm border border-border-subtle bg-surface p-0.5"
    >
      {MODES.map((m) => {
        const selected = m === value
        return (
          <Button
            key={m}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(m)}
            variant={selected ? "default" : "ghost"}
            size="sm"
            className={cn(
              "h-auto rounded-sm px-3 py-1 text-xs font-medium",
              !selected && "text-fg-muted hover:text-fg",
            )}
          >
            {m}
          </Button>
        )
      })}
    </div>
  )
}

function FilterChips() {
  const chips = ["Resource", "Status", "Time range"] as const
  return (
    <div className="flex items-center gap-1.5 rounded-sm border border-border-subtle bg-surface p-0.5">
      <Sparkles className="ml-1.5 size-3.5 text-fg-subtle" aria-hidden />
      {chips.map((c) => (
        <Button
          key={c}
          type="button"
          variant="ghost"
          size="sm"
          className="h-auto gap-1 rounded-sm px-2 py-1 text-xs text-fg-muted hover:text-fg"
        >
          {c}
          <ChevronDown className="size-3" />
        </Button>
      ))}
    </div>
  )
}
