import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"

import { providersApi } from "@/api/endpoints/providers"
import { ProviderTierBadge } from "@/components/common/ProviderTierBadge"
import { cn } from "@/lib/utils"
import type { Provider } from "@/types/entities"
import { AccreditationStatus } from "@/types/enums"

export const Route = createFileRoute("/providers/$providerId")({
  component: ProviderDetailPage,
})

type Tab = "overview" | "accreditation" | "non-compete" | "audit"

function ProviderDetailPage() {
  const { providerId } = Route.useParams()
  const [tab, setTab] = useState<Tab>("overview")

  const query = useQuery({
    queryKey: ["providers", "detail", providerId],
    queryFn: () => providersApi.getById(providerId),
    staleTime: 60_000,
  })

  if (query.isPending) {
    return (
      <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
        <p className="text-fg/70">Loading…</p>
      </div>
    )
  }
  if (query.isError || !query.data) {
    return (
      <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
        <p className="text-fg/70">Couldn&apos;t load this provider.</p>
        <Link to="/providers" className="text-sm text-primary hover:underline">
          ← Back to providers
        </Link>
      </div>
    )
  }

  const p = query.data

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-4xl space-y-4">
        <header className="space-y-2">
          <Link
            to="/providers"
            className="inline-flex h-8 items-center gap-1.5 text-sm text-fg/70 hover:text-fg"
          >
            <ArrowLeft className="h-4 w-4" />
            Providers
          </Link>
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-xl font-semibold text-fg">{p.name}</h1>
            <ProviderTierBadge tier={p.tier} />
            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium border border-fg/20 bg-surface text-fg rounded-none">
              {p.region}
            </span>
          </div>
          <p className="text-sm text-fg/70">
            {p.email ?? "—"} · {p.phone ?? "—"}
          </p>
        </header>

        <nav className="flex gap-1 border-b border-fg/15">
          <TabButton current={tab} value="overview" onClick={setTab}>
            Overview
          </TabButton>
          <TabButton current={tab} value="accreditation" onClick={setTab}>
            Accreditation
          </TabButton>
          <TabButton current={tab} value="non-compete" onClick={setTab}>
            Non-compete ({p.non_compete_clauses.length})
          </TabButton>
          <TabButton current={tab} value="audit" onClick={setTab}>
            Tier transitions ({p.tier_audit?.length ?? 0})
          </TabButton>
        </nav>

        <div className="border border-fg/20 bg-white p-6">
          {tab === "overview" && <OverviewPanel provider={p} />}
          {tab === "accreditation" && <AccreditationPanel provider={p} />}
          {tab === "non-compete" && <NonCompetePanel provider={p} />}
          {tab === "audit" && <AuditPanel provider={p} />}
        </div>
      </div>
    </div>
  )
}

function TabButton({
  current,
  value,
  onClick,
  children,
}: {
  current: Tab
  value: Tab
  onClick: (t: Tab) => void
  children: React.ReactNode
}) {
  const active = current === value
  return (
    <button
      type="button"
      onClick={() => onClick(value)}
      className={cn(
        "px-3 py-2 text-sm border-b-2 -mb-px",
        active ? "border-primary text-fg font-medium" : "border-transparent text-fg/70 hover:text-fg",
      )}
    >
      {children}
    </button>
  )
}

function OverviewPanel({ provider }: { provider: Provider }) {
  return (
    <dl className="grid gap-4 sm:grid-cols-3">
      <div>
        <dt className="text-xs text-fg/60">Tier</dt>
        <dd className="mt-1 text-sm text-fg">{provider.tier}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Region</dt>
        <dd className="mt-1 text-sm text-fg">{provider.region}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Accreditation</dt>
        <dd className="mt-1 text-sm text-fg">{provider.accreditation.status}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Active non-compete clauses</dt>
        <dd className="mt-1 text-sm text-fg">{provider.non_compete_clauses.length}</dd>
      </div>
      <div className="sm:col-span-2">
        <dt className="text-xs text-fg/60">Tier history</dt>
        <dd className="mt-1 text-sm text-fg">
          {provider.tier_audit?.length ?? 0} transitions on file
        </dd>
      </div>
    </dl>
  )
}

const ACCRED_TONE: Record<AccreditationStatus, string> = {
  [AccreditationStatus.ACTIVE]: "text-primary",
  [AccreditationStatus.PENDING_RENEWAL]: "text-danger",
  [AccreditationStatus.EXPIRED]: "text-danger",
  [AccreditationStatus.SUSPENDED]: "text-danger",
}

function AccreditationPanel({ provider }: { provider: Provider }) {
  const a = provider.accreditation
  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      <div>
        <dt className="text-xs text-fg/60">Body</dt>
        <dd className="mt-1 text-sm text-fg">{a.body}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Registration</dt>
        <dd className="mt-1 text-sm text-fg font-mono">{a.registration_number}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Status</dt>
        <dd className={cn("mt-1 text-sm font-medium", ACCRED_TONE[a.status])}>{a.status}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Issued</dt>
        <dd className="mt-1 text-sm text-fg">{a.issued_at}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Expires</dt>
        <dd className="mt-1 text-sm text-fg">{a.expires_at}</dd>
      </div>
    </dl>
  )
}

function NonCompetePanel({ provider }: { provider: Provider }) {
  if (provider.non_compete_clauses.length === 0) {
    return <p className="text-sm text-fg/60">No active non-compete clauses.</p>
  }
  return (
    <ul className="space-y-3">
      {provider.non_compete_clauses.map((nc) => (
        <li key={nc.id} className="border border-fg/15 p-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <p className="text-sm font-semibold text-fg">{nc.client_name}</p>
            <p className="text-xs text-fg/60">
              {nc.start_date} → {nc.end_date}
            </p>
          </div>
          <p className="mt-1 text-xs text-fg/70">
            Regions: {nc.regions.length === 0 ? "Global" : nc.regions.join(", ")}
          </p>
          {nc.notes && <p className="mt-2 text-sm text-fg/80">{nc.notes}</p>}
        </li>
      ))}
    </ul>
  )
}

function AuditPanel({ provider }: { provider: Provider }) {
  const audit = provider.tier_audit ?? []
  if (audit.length === 0) {
    return <p className="text-sm text-fg/60">No tier transitions recorded.</p>
  }
  return (
    <ol className="space-y-3 border-l border-fg/20 pl-4">
      {audit.map((t) => (
        <li key={t.id} className="relative">
          <span
            className="absolute -left-4.75 top-1.5 inline-block h-3 w-3 rounded-full bg-primary"
            aria-hidden
          />
          <p className="text-xs uppercase tracking-wide text-fg/60">
            {new Date(t.at).toLocaleString()} · {t.actor}
          </p>
          <p className="mt-1 text-sm text-fg">
            {t.from_tier ? `${t.from_tier} → ${t.to_tier}` : `Onboarded as ${t.to_tier}`}
          </p>
          <p className="mt-1 text-sm text-fg/70">{t.reason}</p>
        </li>
      ))}
    </ol>
  )
}
