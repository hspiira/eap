import {
  ArrowDown,
  ArrowUp,
  Bell,
  ChevronLeft,
  ChevronRight,
  ChevronRight as Chevron,
  FileText,
  Mail,
  Receipt,
  RefreshCw,
  User,
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

interface SectionCardProps {
  title: string
  link?: string
  className?: string
  children: React.ReactNode
}

function SectionCard({ title, link, className, children }: SectionCardProps) {
  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <CardTitle className="text-sm font-semibold text-fg">{title}</CardTitle>
        {link ? (
          <Button variant="ghost" size="sm" className="-mr-2 h-7 gap-1 px-2 text-fg-muted">
            {link}
            <Chevron className="size-3" />
          </Button>
        ) : null}
      </CardHeader>
      <CardContent className="p-3">{children}</CardContent>
    </Card>
  )
}

const QUICK_APPS = [
  { icon: Mail, label: "Inbox" },
  { icon: FileText, label: "Surveys" },
  { icon: User, label: "Persons" },
  { icon: Receipt, label: "Billing" },
] as const

const ANNOUNCEMENTS = [
  "Q3 reporting cadence: weekly snapshots due each Monday by 09:00.",
  "New incident escalation flow rolling out 2026-06-01.",
  "Care-callback templates updated; review before next campaign.",
] as const

const RECENT_HIRES = [
  { name: "M. Reddy", role: "Care manager", date: "2026-05-08" },
  { name: "L. Achieng", role: "Intake coordinator", date: "2026-05-06" },
  { name: "F. Hasibiri", role: "Senior counsellor", date: "2026-05-02" },
] as const

const TODAYS_QUEUE = [
  { time: "09:00", title: "New tenant onboarding kickoff" },
  { time: "14:00", title: "Internal case review" },
  { time: "15:30", title: "Approval queue: contract renewals" },
] as const

export function HRDashboard() {
  return (
    <div className="mx-auto grid w-full max-w-6xl gap-4 p-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SectionCard title="This week" link="See breakdown">
          <div className="flex items-baseline gap-2">
            <span className="font-mono text-2xl font-semibold tabular-nums text-fg">
              3,320
            </span>
            <Badge variant="secondary" size="sm" className="font-mono tabular-nums text-success">
              <ArrowUp className="size-3" />
              +224
            </Badge>
          </div>
          <div className="my-3 grid grid-cols-3 gap-1 text-xs">
            <BreakdownRow label="Resolved" value="2,459" tone="success" />
            <BreakdownRow label="Pending" value="280" tone="warning" />
            <BreakdownRow label="Escalated" value="56" tone="danger" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            <Stat value="23" label="Approvals" hint="Approved 21 · Pending 2" />
            <Stat value="14" label="Promotions" hint="Promoted 12 · Pending 2" />
            <Stat value="17" label="Movements" hint="On +13 · Off +4" />
          </div>
        </SectionCard>

        <SectionCard title="Today's queue" link="View all">
          <div className="mb-3 flex items-center justify-between rounded-sm border border-border-subtle bg-surface px-2 py-1">
            <Button variant="ghost" size="icon" className="size-6" aria-label="Previous week">
              <ChevronLeft className="size-3.5" />
            </Button>
            <span className="font-mono text-xs tabular-nums text-fg-muted">
              2026-05-08 · W19
            </span>
            <Button variant="ghost" size="icon" className="size-6" aria-label="Next week">
              <ChevronRight className="size-3.5" />
            </Button>
          </div>
          <ul className="grid gap-2">
            {TODAYS_QUEUE.map((item) => (
              <li key={item.time} className="flex items-baseline gap-3 text-sm">
                <span className="font-mono tabular-nums text-fg-subtle">
                  {item.time}
                </span>
                <span className="text-fg">{item.title}</span>
              </li>
            ))}
          </ul>
        </SectionCard>

        <SectionCard title="Quick access">
          <div className="flex items-center gap-3">
            <span
              className="grid size-10 shrink-0 place-items-center rounded-md bg-primary text-primary-foreground font-mono text-sm font-semibold"
              aria-hidden
            >
              EZ
            </span>
            <div className="min-w-0">
              <p className="text-sm font-medium text-fg">Good morning</p>
              <p className="text-xs text-fg-muted">Manager · Admin: All tenants</p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-4 gap-2">
            {QUICK_APPS.map(({ icon: Icon, label }) => (
              <button
                key={label}
                type="button"
                className="grid place-items-center gap-1 rounded-sm border border-border-subtle bg-surface p-2 text-fg-muted transition-colors hover:bg-surface-hover hover:text-fg"
              >
                <Icon className="size-4" />
                <span className="text-[11px]">{label}</span>
              </button>
            ))}
          </div>
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <SectionCard title="Persons" link="View all" className="lg:col-span-1">
          <div className="font-mono text-3xl font-semibold tabular-nums text-fg">
            3,345
          </div>
          <p className="mt-1 text-xs text-fg-muted">Total persons across tenant</p>
          <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
            {[
              { label: "Employees", value: "2,830" },
              { label: "Dependents", value: "456" },
              { label: "Providers", value: "32" },
              { label: "Platform", value: "27" },
            ].map(({ label, value }) => (
              <div
                key={label}
                className="flex justify-between border-b border-border-subtle py-1 last:border-b-0"
              >
                <span className="text-fg-muted">{label}</span>
                <span className="font-mono font-medium tabular-nums text-fg">
                  {value}
                </span>
              </div>
            ))}
          </div>
        </SectionCard>

        <SectionCard title="Alerts" link="Acknowledge" className="lg:col-span-2">
          <div className="flex items-start gap-3">
            <span
              className="grid size-10 shrink-0 place-items-center rounded-md bg-danger-soft font-mono text-sm font-semibold text-danger"
              aria-hidden
            >
              <Bell className="size-4" />
            </span>
            <ul className="grid min-w-0 flex-1 gap-1.5 text-sm text-fg">
              <AlertRow count={13} text="contracts expiring within 30 days" />
              <AlertRow count={23} text="persons missing emergency contact" />
              <AlertRow count={7} text="incidents awaiting case-manager assignment" />
            </ul>
          </div>
        </SectionCard>
      </div>

      <SectionCard title="Recent person changes" link="View all">
        <div className="mb-3 flex flex-wrap gap-2">
          <Button variant="outline" size="sm" className="gap-1.5">
            <RefreshCw className="size-3" />
            Tenant: All
          </Button>
          <Button variant="outline" size="sm">
            By entry date
          </Button>
        </div>
        <div className="mb-4 grid grid-cols-2 gap-3 md:grid-cols-4">
          {[
            { label: "Onboarded", value: "639", positive: true },
            { label: "Off-boarded", value: "320", positive: false },
            { label: "New persons", value: "178", positive: true },
            { label: "Archived", value: "245", positive: false },
          ].map(({ label, value, positive }) => (
            <div
              key={label}
              className="rounded-sm border border-border-subtle bg-surface p-3"
            >
              <div className="font-mono text-xl font-semibold tabular-nums text-fg">
                {value}
              </div>
              <div className="mt-0.5 flex items-center gap-1 text-xs text-fg-muted">
                {positive ? (
                  <ArrowUp className="size-3 text-success" />
                ) : (
                  <ArrowDown className="size-3 text-fg-subtle" />
                )}
                {label}
              </div>
            </div>
          ))}
        </div>
        <div className="border-t border-border-subtle pt-3">
          <div className="mb-2 flex gap-3">
            <button
              type="button"
              className="border-b-2 border-primary pb-1 text-xs font-medium text-fg"
            >
              New persons
            </button>
            <button
              type="button"
              className="border-b-2 border-transparent pb-1 text-xs text-fg-muted hover:text-fg"
            >
              Archived
            </button>
          </div>
          <ul className="grid gap-2">
            {RECENT_HIRES.map((p) => (
              <li
                key={p.name}
                className="flex items-center gap-3 text-sm text-fg"
              >
                <span
                  className="grid size-7 shrink-0 place-items-center rounded-sm bg-muted font-mono text-xs font-medium text-fg-muted"
                  aria-hidden
                >
                  {p.name.slice(0, 1)}
                </span>
                <span className="flex-1 truncate">
                  <span className="font-medium">{p.name}</span>
                  <span className="text-fg-muted"> · {p.role}</span>
                </span>
                <span className="font-mono text-xs tabular-nums text-fg-subtle">
                  {p.date}
                </span>
              </li>
            ))}
          </ul>
        </div>
      </SectionCard>

      <SectionCard title="Announcements" link="View all">
        <ul className="grid gap-2 text-sm text-fg">
          {ANNOUNCEMENTS.map((text, i) => (
            <li
              key={i}
              className="border-b border-border-subtle pb-2 last:border-b-0 last:pb-0"
            >
              <button
                type="button"
                className="text-left text-fg-muted transition-colors hover:text-primary"
              >
                {text}
              </button>
            </li>
          ))}
        </ul>
      </SectionCard>
    </div>
  )
}

function BreakdownRow({
  label,
  value,
  tone,
}: {
  label: string
  value: string
  tone: "success" | "warning" | "danger"
}) {
  const toneClass: Record<typeof tone, string> = {
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-danger",
  }
  return (
    <div className="flex items-center gap-2 rounded-sm border border-border-subtle bg-surface px-2 py-1.5">
      <span className={cn("size-1.5 rounded-full", toneClass[tone])} aria-hidden />
      <span className="text-fg-muted">{label}</span>
      <span className="ml-auto font-mono font-medium tabular-nums text-fg">
        {value}
      </span>
    </div>
  )
}

function Stat({
  value,
  label,
  hint,
}: {
  value: string
  label: string
  hint?: string
}) {
  return (
    <div className="rounded-sm border border-border-subtle bg-surface p-2 text-center">
      <div className="font-mono text-base font-semibold tabular-nums text-fg">
        {value}
      </div>
      <div className="text-[11px] text-fg-muted">{label}</div>
      {hint ? (
        <div className="mt-0.5 text-[10px] text-fg-subtle">{hint}</div>
      ) : null}
    </div>
  )
}

function AlertRow({ count, text }: { count: number; text: string }) {
  return (
    <li className="flex items-baseline gap-2">
      <span className="font-mono font-medium tabular-nums text-danger">
        {count}
      </span>
      <span className="text-fg-muted">{text}</span>
    </li>
  )
}
