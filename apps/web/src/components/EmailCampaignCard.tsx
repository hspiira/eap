import { Mail } from "lucide-react"

import { Panel } from "@/components/common/Panel"
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
    <Panel
      icon={Mail}
      title={title}
      subtitle={subtitle}
      badge={
        <span className="inline-flex items-center gap-1 rounded-sm border border-success/30 bg-success-soft px-1.5 py-0.5 text-[11px] font-medium text-success-fg">
          <span className="size-1.5 rounded-full bg-success" aria-hidden />
          Live
        </span>
      }
      className={className}
      bodyClassName="grid grid-cols-1 sm:grid-cols-2"
    >
      {sections.map((s, i) => (
        <SectionBlock
          key={s.title}
          section={s}
          isFirstColumn={i === 0}
          totalCols={sections.length}
        />
      ))}
    </Panel>
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
        "p-3.5",
        !isFirstColumn && "border-t border-fg/8 sm:border-t-0",
        !isFirstColumn && totalCols > 1 && "sm:border-l sm:border-l-fg/8",
      )}
    >
      <div className="text-xs font-semibold tracking-wide text-fg/55">
        {section.title}
      </div>
      <div className="mt-1 flex items-baseline gap-2">
        <span className="font-mono text-2xl font-semibold tabular-nums text-fg">
          {section.primaryMetric}
        </span>
        {section.primaryHint ? (
          <span className="text-xs text-fg/45">{section.primaryHint}</span>
        ) : null}
      </div>
      <ul className="mt-3 grid gap-1.5">
        {section.rows.map((r) => (
          <li
            key={r.label}
            className="flex items-center justify-between text-xs"
          >
            <span className="flex items-center gap-2 text-fg/65">
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
