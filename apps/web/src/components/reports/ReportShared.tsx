
import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowLeft,
  FileBarChart,
} from "lucide-react"

import { EmptyState } from "@/components/common/EmptyState"
import { PageShell } from "@/components/common/PageShell"
import { cn } from "@/lib/utils"

export function ReportSection({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section>
      <h3 className="text-sm font-semibold text-fg">{title}</h3>
      {children}
    </section>
  )
}

export function Field({
  label,
  value,
}: {
  label: string
  value: React.ReactNode
}) {
  return (
    <div>
      <dt className="text-[11px] font-semibold tracking-wide text-fg/55">
        {label}
      </dt>
      <dd className="mt-0.5 text-sm text-fg">{value}</dd>
    </div>
  )
}

export function SummaryStat({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string
  value: number
  hint?: string
  tone?: "default" | "danger"
}) {
  const isDanger = tone === "danger"
  return (
    <div
      className={cn(
        "rounded-sm border bg-bg px-3 py-2 print:bg-white",
        isDanger ? "border-danger/30 bg-danger-soft" : "border-fg/15",
      )}
    >
      <div
        className={cn(
          "flex items-center gap-1 text-[10px] font-semibold tracking-wide",
          isDanger ? "text-danger-fg" : "text-fg/55",
        )}
      >
        {isDanger ? <AlertTriangle className="size-3" /> : null}
        {label}
      </div>
      <div className="mt-0.5 flex items-baseline gap-2">
        <span
          className={cn(
            "font-mono text-lg font-semibold",
            isDanger ? "text-danger-fg" : "text-fg",
          )}
        >
          {value}
        </span>
        {hint ? (
          <span className="font-mono text-[11px] text-fg/55">{hint}</span>
        ) : null}
      </div>
    </div>
  )
}

export function BackLink() {
  return (
    <Link
      to="/reports"
      className="inline-flex h-7 items-center gap-1 rounded-sm px-2 text-xs text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
    >
      <ArrowLeft className="size-3.5" />
      Reports
    </Link>
  )
}

export function UnknownTemplate({ slug }: { slug: string }) {
  return (
    <PageShell icon={FileBarChart} breadcrumb={`Reports · ${slug}`}>
      <EmptyState
        icon={FileBarChart}
        title="Template not available"
        description={
          <>
            The template <span className="font-mono text-fg">{slug}</span> isn&apos;t
            implemented yet. Phase 3 will ship the wave-summary, tier-portfolio, and
            anchor-cohort templates.
          </>
        }
        action={
          <Link
            to="/reports"
            className="inline-flex h-9 items-center gap-1.5 rounded-sm border border-fg/15 bg-surface px-3 text-sm font-medium text-fg hover:bg-surface-hover"
          >
            <ArrowLeft className="size-4" />
            Back to reports
          </Link>
        }
      />
    </PageShell>
  )
}
