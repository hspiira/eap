import {
  AlertTriangle,
  CalendarClock,
  CheckCircle2,
  FileSignature,
  MessageSquare,
  Settings,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

type ActivityTone = "info" | "success" | "warning" | "danger"

interface Activity {
  id: string
  icon: React.ElementType
  tone: ActivityTone
  title: string
  description: string
  time: string
  badge?: { label: string; variant?: "default" | "secondary" | "destructive" | "outline" }
  actions?: React.ReactNode
}

const TABS = ["All", "Sessions", "Cases", "Contracts"] as const

const ACTIVITIES: Activity[] = [
  {
    id: "1",
    icon: CalendarClock,
    tone: "info",
    title: "Weekly summary",
    description: "12 sessions delivered, 3 case openings, 1 critical incident.",
    time: "Today",
    badge: { label: "Cycle complete", variant: "secondary" },
  },
  {
    id: "2",
    icon: FileSignature,
    tone: "warning",
    title: "Contract renewal due",
    description: "Acme Holdings — current term expires in 14 days.",
    time: "Yesterday",
    actions: (
      <>
        <Button variant="outline" size="sm">
          Defer
        </Button>
        <Button size="sm">
          <CheckCircle2 className="size-3.5" />
          Renew
        </Button>
      </>
    ),
  },
  {
    id: "3",
    icon: AlertTriangle,
    tone: "danger",
    title: "Critical incident logged",
    description: "Severity: High. Awaiting case-manager assignment.",
    time: "Yesterday",
    badge: { label: "Action needed", variant: "destructive" },
  },
  {
    id: "4",
    icon: MessageSquare,
    tone: "success",
    title: "Survey completed",
    description: "12 respondents over the past 24 hours.",
    time: "2d ago",
  },
]

const TONE_RING: Record<ActivityTone, string> = {
  info: "bg-info-soft text-info ring-info/20",
  success: "bg-success-soft text-success ring-success/20",
  warning: "bg-warning-soft text-warning ring-warning/20",
  danger: "bg-danger-soft text-danger ring-danger/20",
}

export function ActivityFeedCard() {
  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border p-3">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-semibold text-fg">
            Activity feed
          </CardTitle>
          <Badge variant="secondary" size="sm" className="font-mono tabular-nums">
            {ACTIVITIES.length}
          </Badge>
        </div>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Activity feed settings"
          className="size-8"
        >
          <Settings className="size-4" />
        </Button>
      </CardHeader>

      <div
        role="tablist"
        aria-label="Activity filters"
        className="flex border-b border-border"
      >
        {TABS.map((tab, i) => {
          const active = i === 0
          return (
            <button
              key={tab}
              type="button"
              role="tab"
              aria-selected={active}
              className={cn(
                "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "border-primary text-fg"
                  : "border-transparent text-fg-muted hover:text-fg",
              )}
            >
              {tab}
            </button>
          )
        })}
      </div>

      <CardContent className="p-0">
        <ol className="divide-y divide-border">
          {ACTIVITIES.map((a) => (
            <li key={a.id} className="flex gap-3 p-3">
              <span
                className={cn(
                  "flex size-9 shrink-0 items-center justify-center rounded-md ring-1",
                  TONE_RING[a.tone],
                )}
                aria-hidden
              >
                <a.icon className="size-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-fg">{a.title}</span>
                  {a.badge ? (
                    <Badge variant={a.badge.variant ?? "secondary"} size="sm">
                      {a.badge.label}
                    </Badge>
                  ) : null}
                  <span className="ml-auto shrink-0 font-mono text-xs tabular-nums text-fg-subtle">
                    {a.time}
                  </span>
                </div>
                <p className="mt-0.5 text-sm text-fg-muted">{a.description}</p>
                {a.actions ? (
                  <div className="mt-2 flex gap-2">{a.actions}</div>
                ) : null}
              </div>
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  )
}
