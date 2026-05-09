import { useState } from "react"

import { BookOpen, ChevronDown, ChevronUp } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { cn } from "@/lib/utils"

interface ToggleSetting {
  id: string
  label: string
  description?: string
  defaultEnabled?: boolean
}

interface MapSettingsCardProps {
  settings?: ReadonlyArray<ToggleSetting>
  className?: string
}

const DEFAULT_SETTINGS: ReadonlyArray<ToggleSetting> = [
  {
    id: "auto-assign",
    label: "Auto-assign new cases",
    description: "Route new cases to available case managers based on workload.",
    defaultEnabled: true,
  },
  {
    id: "weekly-digest",
    label: "Weekly digest emails",
    description: "Send a Monday summary of the previous week's activity.",
    defaultEnabled: true,
  },
  {
    id: "audit-export",
    label: "Audit log retention 90d",
    description: "Keep audit log entries for 90 days before archival.",
    defaultEnabled: false,
  },
]

export function MapSettingsCard({
  settings = DEFAULT_SETTINGS,
  className,
}: MapSettingsCardProps = {}) {
  const initial = Object.fromEntries(
    settings.map((s) => [s.id, s.defaultEnabled ?? false]),
  )
  const [enabled, setEnabled] = useState<Record<string, boolean>>(initial)

  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <CardTitle className="text-sm font-semibold text-fg">
          Workspace settings
        </CardTitle>
        <Button
          asChild
          variant="ghost"
          size="sm"
          className="-mr-2 h-7 gap-1.5 px-2 text-xs text-fg-muted"
        >
          <a href="#docs">
            <BookOpen className="size-3" />
            Docs
          </a>
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <ul className="divide-y divide-border-subtle">
          {settings.map((s) => (
            <SettingRow
              key={s.id}
              setting={s}
              enabled={enabled[s.id] ?? false}
              onToggle={(v) =>
                setEnabled((prev) => ({ ...prev, [s.id]: v }))
              }
            />
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}

function SettingRow({
  setting,
  enabled,
  onToggle,
}: {
  setting: ToggleSetting
  enabled: boolean
  onToggle: (next: boolean) => void
}) {
  const [open, setOpen] = useState(false)
  return (
    <li className="p-3">
      <Collapsible open={open} onOpenChange={setOpen}>
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-fg">{setting.label}</span>
              {setting.description ? (
                <CollapsibleTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-5 text-fg-muted"
                    aria-label={open ? "Collapse details" : "Expand details"}
                  >
                    {open ? (
                      <ChevronUp className="size-3" />
                    ) : (
                      <ChevronDown className="size-3" />
                    )}
                  </Button>
                </CollapsibleTrigger>
              ) : null}
            </div>
          </div>
          <Toggle enabled={enabled} onChange={onToggle} label={setting.label} />
        </div>
        {setting.description ? (
          <CollapsibleContent className="pt-1.5">
            <p className="text-xs text-fg-muted">{setting.description}</p>
          </CollapsibleContent>
        ) : null}
      </Collapsible>
    </li>
  )
}

function Toggle({
  enabled,
  onChange,
  label,
}: {
  enabled: boolean
  onChange: (next: boolean) => void
  label: string
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      aria-label={label}
      onClick={() => onChange(!enabled)}
      className={cn(
        "relative inline-flex h-5 w-8 shrink-0 cursor-pointer items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg",
        enabled ? "bg-primary" : "bg-muted",
      )}
    >
      <span
        className={cn(
          "size-4 rounded-full bg-bg shadow-sm transition-transform",
          enabled ? "translate-x-3.5" : "translate-x-0.5",
        )}
        aria-hidden
      />
    </button>
  )
}
