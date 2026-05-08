import { Info } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface CampaignMetric {
  label: string
  value: string
  dot?: "success" | "warning" | "danger" | null
}

interface CampaignSection {
  title: string
  primaryMetric: string
  primaryHint?: string
  rows: ReadonlyArray<CampaignMetric>
}

interface EmailCampaignCardProps {
  title?: string
  subtitle?: string
  sections?: ReadonlyArray<CampaignSection>
  className?: string
}

const DEFAULT_SECTIONS: ReadonlyArray<CampaignSection> = [
  {
    title: "Delivered",
    primaryMetric: "98.0%",
    primaryHint: "Of sent emails",
    rows: [
      { label: "Sent", value: "415,581" },
      { label: "Delivered", value: "407,269" },
      { label: "Bounced", value: "8,312", dot: "warning" },
    ],
  },
  {
    title: "Engaged",
    primaryMetric: "32.4%",
    primaryHint: "Open rate",
    rows: [
      { label: "Opened", value: "131,955", dot: "success" },
      { label: "Clicked", value: "27,402" },
      { label: "Unsubscribed", value: "1,182", dot: "danger" },
    ],
  },
]

const DOT_TONE: Record<NonNullable<CampaignMetric["dot"]>, string> = {
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
}

export function EmailCampaignCard({
  title = "Outreach campaign",
  subtitle = "Wellness check-in · Q2 2026",
  sections = DEFAULT_SECTIONS,
  className,
}: EmailCampaignCardProps = {}) {
  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-start justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <div>
          <CardTitle className="text-sm font-semibold text-fg">
            {title}
          </CardTitle>
          <p className="mt-0.5 text-xs text-fg-muted">{subtitle}</p>
        </div>
        <Badge variant="outline" size="sm">
          <Info className="size-3" />
          Live
        </Badge>
      </CardHeader>
      <CardContent className="grid gap-0 p-0 sm:grid-cols-2">
        {sections.map((s, i) => (
          <SectionBlock
            key={s.title}
            section={s}
            isFirstColumn={i === 0}
            totalCols={sections.length}
          />
        ))}
      </CardContent>
    </Card>
  )
}

function SectionBlock({
  section,
  isFirstColumn,
  totalCols,
}: {
  section: CampaignSection
  isFirstColumn: boolean
  totalCols: number
}) {
  return (
    <div
      className={cn(
        "p-4",
        !isFirstColumn && "border-t border-border-subtle sm:border-t-0",
        !isFirstColumn && totalCols > 1 && "sm:border-l sm:border-l-border-subtle",
      )}
    >
      <div className="text-xs font-medium uppercase tracking-wide text-fg-muted">
        {section.title}
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="font-mono text-2xl font-semibold tabular-nums text-fg">
          {section.primaryMetric}
        </span>
        {section.primaryHint ? (
          <span className="text-xs text-fg-subtle">{section.primaryHint}</span>
        ) : null}
      </div>
      <ul className="mt-3 grid gap-1.5">
        {section.rows.map((r) => (
          <li
            key={r.label}
            className="flex items-center justify-between text-xs"
          >
            <span className="flex items-center gap-2 text-fg-muted">
              {r.dot ? (
                <span
                  className={cn("size-1.5 rounded-full", DOT_TONE[r.dot])}
                  aria-hidden
                />
              ) : (
                <span className="size-1.5" aria-hidden />
              )}
              {r.label}
            </span>
            <span className="font-mono font-medium tabular-nums text-fg">
              {r.value}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
