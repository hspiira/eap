import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"

import { providersApi } from "@/api/endpoints/providers"
import { ProviderTierBadge } from "@/components/common/ProviderTierBadge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ProviderRegion, ProviderTier } from "@/types/enums"

const REGIONS = Object.values(ProviderRegion)
const TIERS = Object.values(ProviderTier)

function isTier(v: unknown): v is ProviderTier {
  return typeof v === "string" && (TIERS as string[]).includes(v)
}
function isRegion(v: unknown): v is ProviderRegion {
  return typeof v === "string" && (REGIONS as string[]).includes(v)
}

export const Route = createFileRoute("/providers/")({
  component: ProvidersListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { tier?: ProviderTier; region?: ProviderRegion } = {}
    if (isTier(search.tier)) out.tier = search.tier
    if (isRegion(search.region)) out.region = search.region
    return out
  },
})

function ProvidersListPage() {
  const params = useSearch({ from: "/providers/" })
  const navigate = useNavigate({ from: "/providers/" })
  const [page] = useState(1)

  const query = useQuery({
    queryKey: ["providers", "list", { page, tier: params.tier, region: params.region }],
    queryFn: () => providersApi.list({ tier: params.tier, region: params.region, page, limit: 50 }),
    staleTime: 60_000,
  })

  const items = query.data?.items ?? []

  const setTier = (v: string) => {
    const tier = isTier(v) ? v : undefined
    navigate({ search: (prev) => ({ ...prev, tier }), replace: true })
  }
  const setRegion = (v: string) => {
    const region = isRegion(v) ? v : undefined
    navigate({ search: (prev) => ({ ...prev, region }), replace: true })
  }

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-5xl space-y-4">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-xl font-semibold text-fg">Providers</h1>
            <p className="mt-1 text-sm text-fg/70">
              Counsellors, agencies, and clinics on the panel — tier T1/T2/T3 and region.
            </p>
          </div>
          <div className="flex gap-2">
            <Select value={params.tier ?? "all"} onValueChange={setTier}>
              <SelectTrigger className="rounded-none h-9 w-30 border-fg/30 bg-white text-fg [&>svg]:text-fg">
                <SelectValue placeholder="All tiers" />
              </SelectTrigger>
              <SelectContent className="rounded-none border-fg/30 bg-white">
                <SelectItem value="all" className="rounded-none">
                  All tiers
                </SelectItem>
                {TIERS.map((t) => (
                  <SelectItem key={t} value={t} className="rounded-none">
                    {t}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={params.region ?? "all"} onValueChange={setRegion}>
              <SelectTrigger className="rounded-none h-9 w-45 border-fg/30 bg-white text-fg [&>svg]:text-fg">
                <SelectValue placeholder="All regions" />
              </SelectTrigger>
              <SelectContent className="rounded-none border-fg/30 bg-white">
                <SelectItem value="all" className="rounded-none">
                  All regions
                </SelectItem>
                {REGIONS.map((r) => (
                  <SelectItem key={r} value={r} className="rounded-none">
                    {r}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </header>

        {query.isPending ? (
          <p className="text-sm text-fg/60">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-sm text-fg/60">No providers match the current filters.</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2">
            {items.map((p) => (
              <li key={p.id}>
                <Link
                  to="/providers/$providerId"
                  params={{ providerId: p.id }}
                  className="flex h-full flex-col gap-2 border border-fg/20 bg-white p-4 hover:border-primary hover:bg-surface/30"
                >
                  <div className="flex items-start justify-between gap-3">
                    <h2 className="text-sm font-semibold text-fg">{p.name}</h2>
                    <ProviderTierBadge tier={p.tier} />
                  </div>
                  <p className="text-xs text-fg/60">{p.region}</p>
                  <p className="text-xs text-fg/70">
                    {p.accreditation.body} · {p.accreditation.registration_number}
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
