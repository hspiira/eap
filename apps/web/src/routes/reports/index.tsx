import { createFileRoute, Link } from "@tanstack/react-router"
import {
  ArrowRight,
  FileBarChart,
  FileText,
  type LucideIcon,
  PieChart,
  Ribbon,
  Sparkles,
} from "lucide-react"

import { PageShell } from "@/components/common/PageShell"
import { cn } from "@/lib/utils"

export const Route = createFileRoute("/reports/")({
  component: ReportsLandingPage,
})

interface ReportTemplate {
  slug: string
  title: string
  description: string
  cadence: string
  icon: LucideIcon
  ready: boolean
}

const TEMPLATES: ReportTemplate[] = [
  {
    slug: "per-client-renewal",
    title: "Per-client renewal pack",
    description:
      "Sessions by month, diagnosis prevalence, care-callback outcomes, satisfaction distribution.",
    cadence: "Annual / on-renewal",
    icon: FileText,
    ready: true,
  },
  {
    slug: "care-callback-summary",
    title: "Care callback wave summary",
    description:
      "PHQ-9 / WOS-5 deltas, crisis-flag count, by-counsellor outcomes for a single wave.",
    cadence: "Per wave",
    icon: PieChart,
    ready: true,
  },
  {
    slug: "tier-portfolio",
    title: "Tier-portfolio snapshot",
    description: "Active clients by Tier A/B/C, contract values, renewal-window heatmap.",
    cadence: "Monthly",
    icon: Ribbon,
    ready: false,
  },
  {
    slug: "anchor-cohort-benchmark",
    title: "Anchor-cohort benchmark",
    description:
      "Cross-tenant aggregate (k-floor 10) for benchmarking against the anchor cohort.",
    cadence: "Quarterly",
    icon: Sparkles,
    ready: false,
  },
]

function ReportsLandingPage() {
  return (
    <PageShell icon={FileBarChart} breadcrumb="Reports">
      <div className="min-h-0 flex-1 overflow-y-auto bg-bg">
        <div className="mx-auto max-w-5xl space-y-5 px-5 py-5">
          <header>
            <h1 className="text-base font-semibold text-fg">Templates</h1>
            <p className="mt-1 text-xs text-fg/60">
              Reference templates for renewal, wave summaries, and tier portfolio reviews.
            </p>
          </header>

          <ul className="grid gap-3 sm:grid-cols-2">
            {TEMPLATES.map((tpl) => (
              <li key={tpl.slug}>
                <ReportTemplateCard template={tpl} />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </PageShell>
  )
}

function ReportTemplateCard({ template }: { template: ReportTemplate }) {
  const Icon = template.icon
  const base =
    "group flex h-full flex-col gap-3 rounded-sm border border-fg/10 bg-surface p-4 transition-colors"

  if (!template.ready) {
    return (
      <div className={cn(base, "opacity-60")} aria-disabled="true">
        <CardHeader template={template} icon={Icon} />
        <p className="text-sm text-fg/65">{template.description}</p>
        <span className="mt-auto inline-flex items-center rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-fg/55">
          Coming soon
        </span>
      </div>
    )
  }

  return (
    <Link
      to="/reports/$templateSlug"
      params={{ templateSlug: template.slug }}
      className={cn(base, "hover:border-fg/25 hover:bg-surface-hover")}
    >
      <CardHeader template={template} icon={Icon} />
      <p className="text-sm text-fg/65">{template.description}</p>
      <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-primary">
        Open template <ArrowRight className="size-3.5" />
      </span>
    </Link>
  )
}

function CardHeader({
  template,
  icon: Icon,
}: {
  template: ReportTemplate
  icon: LucideIcon
}) {
  return (
    <div className="flex items-start gap-3">
      <span
        aria-hidden
        className="grid size-8 shrink-0 place-items-center rounded-sm bg-primary/10 text-primary"
      >
        <Icon className="size-4" />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="text-sm font-semibold text-fg">{template.title}</h2>
        <p className="text-[11px] text-fg/55">{template.cadence}</p>
      </div>
    </div>
  )
}
