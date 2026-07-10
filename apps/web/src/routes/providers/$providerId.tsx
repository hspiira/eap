import { useState } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { ArrowLeft } from "lucide-react"

import { nonCompeteClausesApi } from "@/api/endpoints/non-compete-clauses"
import { providersApi } from "@/api/endpoints/providers"
import { ProviderTierBadge } from "@/components/common/ProviderTierBadge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { normalizeErrorMessage } from "@/lib/errors"
import { cn } from "@/lib/utils"
import type { NonCompeteClause, Provider } from "@/types/entities"
import {
  AccreditationStatus,
  NonCompeteStatus,
  PanelStatus,
} from "@/types/enums"

export const Route = createFileRoute("/providers/$providerId")({
  component: ProviderDetailPage,
})

type Tab = "overview" | "accreditation" | "non-compete"

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
  const profile = p.provider_profile

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
            <h1 className="font-mono text-base font-semibold text-fg">{p.id}</h1>
            <ProviderTierBadge tier={profile.tier} />
            <span className="inline-flex items-center px-2 py-0.5 text-xs font-medium border border-fg/20 bg-surface text-fg rounded-none">
              {profile.region}
            </span>
            <span
              className={cn(
                "inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-none",
                profile.panel_status === PanelStatus.ACTIVE
                  ? "border border-primary/30 bg-primary/10 text-primary"
                  : "border border-danger/30 bg-danger-soft text-danger-fg",
              )}
            >
              Panel: {profile.panel_status}
            </span>
          </div>
          {profile.bio ? (
            <p className="text-sm text-fg/70">{profile.bio}</p>
          ) : null}
        </header>

        <nav className="flex gap-1 border-b border-fg/15">
          <TabButton current={tab} value="overview" onClick={setTab}>
            Overview
          </TabButton>
          <TabButton current={tab} value="accreditation" onClick={setTab}>
            Accreditation
          </TabButton>
          <TabButton current={tab} value="non-compete" onClick={setTab}>
            Non-compete
          </TabButton>
        </nav>

        <div className="border border-fg/20 bg-white p-6">
          {tab === "overview" && <OverviewPanel provider={p} />}
          {tab === "accreditation" && <AccreditationPanel provider={p} />}
          {tab === "non-compete" && <NonCompetePanel provider={p} />}
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
    <Button
      type="button"
      variant="ghost"
      onClick={() => onClick(value)}
      className={cn(
        "h-auto rounded-none border-b-2 px-3 py-2 text-sm hover:bg-transparent -mb-px",
        active ? "border-primary text-fg font-medium" : "border-transparent text-fg/70 hover:text-fg",
      )}
    >
      {children}
    </Button>
  )
}

function OverviewPanel({ provider }: { provider: Provider }) {
  const profile = provider.provider_profile
  return (
    <dl className="grid gap-4 sm:grid-cols-3">
      <div>
        <dt className="text-xs text-fg/60">Tier</dt>
        <dd className="mt-1 text-sm text-fg">{profile.tier}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Region</dt>
        <dd className="mt-1 text-sm text-fg">{profile.region}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Panel status</dt>
        <dd className="mt-1 text-sm text-fg">{profile.panel_status}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Accreditation</dt>
        <dd className="mt-1 text-sm text-fg">{profile.accreditation_status}</dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Specialties</dt>
        <dd className="mt-1 text-sm text-fg">
          {profile.specialties.length === 0
            ? "—"
            : profile.specialties.join(", ")}
        </dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Person status</dt>
        <dd className="mt-1 text-sm text-fg">{provider.status}</dd>
      </div>
    </dl>
  )
}

const ACCRED_TONE: Record<AccreditationStatus, string> = {
  [AccreditationStatus.ACCREDITED]: "text-primary",
  [AccreditationStatus.PENDING]: "text-fg/70",
  [AccreditationStatus.LAPSED]: "text-danger",
  [AccreditationStatus.SUSPENDED]: "text-danger",
  [AccreditationStatus.REJECTED]: "text-danger",
}

function AccreditationPanel({ provider }: { provider: Provider }) {
  const profile = provider.provider_profile
  return (
    <dl className="grid gap-4 sm:grid-cols-2">
      <div>
        <dt className="text-xs text-fg/60">Authority</dt>
        <dd className="mt-1 text-sm text-fg">
          {profile.accreditation_authority ?? "—"}
        </dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Status</dt>
        <dd className={cn("mt-1 text-sm font-medium", ACCRED_TONE[profile.accreditation_status])}>
          {profile.accreditation_status}
        </dd>
      </div>
      <div>
        <dt className="text-xs text-fg/60">Expiry</dt>
        <dd className="mt-1 text-sm text-fg">
          {profile.accreditation_expiry ?? "—"}
        </dd>
      </div>
      {provider.license_info ? (
        <>
          <div>
            <dt className="text-xs text-fg/60">License number</dt>
            <dd className="mt-1 text-sm text-fg font-mono">
              {provider.license_info.number ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-fg/60">Issuing authority</dt>
            <dd className="mt-1 text-sm text-fg">
              {provider.license_info.issuing_authority ?? "—"}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-fg/60">License expires</dt>
            <dd className="mt-1 text-sm text-fg">
              {provider.license_info.expiry_date ?? "—"}
            </dd>
          </div>
        </>
      ) : null}
    </dl>
  )
}

function NonCompetePanel({ provider }: { provider: Provider }) {
  const queryClient = useQueryClient()
  const toast = useToast()

  const list = useQuery({
    queryKey: ["non-compete", "list", provider.id],
    queryFn: () => nonCompeteClausesApi.listForProvider(provider.id),
    staleTime: 30_000,
  })

  const refetch = () => {
    queryClient.invalidateQueries({ queryKey: ["non-compete", "list", provider.id] })
    queryClient.invalidateQueries({ queryKey: ["providers", "detail", provider.id] })
  }

  if (list.isPending) {
    return <p className="text-sm text-fg/60">Loading non-compete clauses…</p>
  }
  if (list.isError) {
    return (
      <p className="text-sm text-danger-fg">
        {normalizeErrorMessage(list.error, "Could not load non-compete clauses")}
      </p>
    )
  }
  const clauses = list.data ?? []
  if (clauses.length === 0) {
    return (
      <p className="text-sm text-fg/60">
        No non-compete clauses on file. Use the API or the upcoming dialog to draft one.
      </p>
    )
  }

  return (
    <ul className="space-y-3">
      {clauses.map((nc) => (
        <NonCompeteRow key={nc.id} clause={nc} onChanged={refetch} toastError={(m) => toast.showError(m)} toastSuccess={(m) => toast.showSuccess(m)} />
      ))}
    </ul>
  )
}

function NonCompeteRow({
  clause,
  onChanged,
  toastError,
  toastSuccess,
}: {
  clause: NonCompeteClause
  onChanged: () => void
  toastError: (m: string) => void
  toastSuccess: (m: string) => void
}) {
  const [revokeReason, setRevokeReason] = useState("")
  const [revokeOpen, setRevokeOpen] = useState(false)

  const sign = useMutation({
    mutationFn: () => nonCompeteClausesApi.sign(clause.id, { signed_by: clause.tenant_id }),
    onSuccess: () => {
      toastSuccess("Clause signed")
      onChanged()
    },
    onError: (e) => toastError(normalizeErrorMessage(e, "Could not sign clause")),
  })

  const revoke = useMutation({
    mutationFn: () => nonCompeteClausesApi.revoke(clause.id, { reason: revokeReason.trim() }),
    onSuccess: () => {
      toastSuccess("Clause revoked")
      setRevokeOpen(false)
      setRevokeReason("")
      onChanged()
    },
    onError: (e) => toastError(normalizeErrorMessage(e, "Could not revoke clause")),
  })

  return (
    <li className="border border-fg/15 p-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-semibold text-fg">{clause.terms_summary}</p>
        <span
          className={cn(
            "inline-flex items-center px-1.5 py-0.5 text-xs font-medium rounded-none",
            clause.status === NonCompeteStatus.ACTIVE
              ? "border border-primary/30 bg-primary/10 text-primary"
              : clause.status === NonCompeteStatus.REVOKED || clause.status === NonCompeteStatus.EXPIRED
                ? "border border-fg/20 bg-bg text-fg/70"
                : "border border-fg/20 bg-bg text-fg",
          )}
        >
          {clause.status}
        </span>
      </div>
      <p className="mt-1 text-xs text-fg/60">
        Effective {clause.effective_from} → {clause.effective_until ?? "indefinite"}
      </p>
      {clause.revoked_reason ? (
        <p className="mt-2 text-xs text-fg/70">Revoked: {clause.revoked_reason}</p>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        {clause.status === NonCompeteStatus.DRAFT ? (
          <Button
            type="button"
            size="sm"
            onClick={() => sign.mutate()}
            disabled={sign.isPending}
          >
            {sign.isPending ? "Signing…" : "Sign"}
          </Button>
        ) : null}
        {clause.status === NonCompeteStatus.ACTIVE && !revokeOpen ? (
          <Button
            type="button"
            size="sm"
            variant="outline"
            onClick={() => setRevokeOpen(true)}
          >
            Revoke
          </Button>
        ) : null}
      </div>

      {revokeOpen ? (
        <div className="mt-3 grid gap-2 border-t border-fg/10 pt-3">
          <label htmlFor={`revoke-${clause.id}`} className="text-xs text-fg/60">
            Reason for revoking
          </label>
          <Input
            id={`revoke-${clause.id}`}
            type="text"
            value={revokeReason}
            onChange={(e) => setRevokeReason(e.target.value)}
            placeholder="e.g. provider transitioned to a different client portfolio"
          />
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              onClick={() => revoke.mutate()}
              disabled={!revokeReason.trim() || revoke.isPending}
            >
              {revoke.isPending ? "Revoking…" : "Confirm revoke"}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                setRevokeOpen(false)
                setRevokeReason("")
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : null}
    </li>
  )
}

