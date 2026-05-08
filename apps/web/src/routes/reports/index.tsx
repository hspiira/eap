import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowRight, FileText, type LucideIcon, PieChart, Ribbon, Sparkles } from "lucide-react"

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
    ready: false,
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
    description: "Cross-tenant aggregate (k-floor 10) for benchmarking against the anchor cohort.",
    cadence: "Quarterly",
    icon: Sparkles,
    ready: false,
  },
]

function ReportsLandingPage() {
  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex items-baseline justify-between gap-4">
          <div>
            <h1 className="text-2xl font-semibold text-ink">Reports</h1>
            <p className="mt-1 text-sm text-ink/70">
              Reference templates for renewal, wave summaries, and tier portfolio reviews.
            </p>
          </div>
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
  )
}

function ReportTemplateCard({ template }: { template: ReportTemplate }) {
  const Icon = template.icon
  const cardClass =
    "group flex h-full flex-col gap-3 border border-ink/20 bg-white p-4 rounded-none transition-colors"

  if (!template.ready) {
    return (
      <div className={`${cardClass} opacity-60`} aria-disabled="true">
        <CardHeader template={template} icon={Icon} />
        <p className="text-sm text-ink/70">{template.description}</p>
        <span className="mt-auto text-xs uppercase tracking-wide text-ink/50">Coming soon</span>
      </div>
    )
  }

  return (
    <Link
      to="/reports/$templateSlug"
      params={{ templateSlug: template.slug }}
      className={`${cardClass} hover:border-natural hover:bg-warm/30`}
    >
      <CardHeader template={template} icon={Icon} />
      <p className="text-sm text-ink/70">{template.description}</p>
      <span className="mt-auto inline-flex items-center gap-1 text-sm font-medium text-natural">
        Open template <ArrowRight className="h-4 w-4" />
      </span>
    </Link>
  )
}

function CardHeader({ template, icon: Icon }: { template: ReportTemplate; icon: LucideIcon }) {
  return (
    <div className="flex items-start gap-3">
      <span className="flex h-9 w-9 shrink-0 items-center justify-center border border-ink/20 bg-warm/40 text-natural">
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="text-sm font-semibold text-ink">{template.title}</h2>
        <p className="text-xs text-ink/60">{template.cadence}</p>
      </div>
    </div>
  )
}
