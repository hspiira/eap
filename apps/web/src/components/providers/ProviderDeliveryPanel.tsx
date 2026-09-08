import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { providersApi } from "@/api/endpoints/providers"
import { RailSection } from "@/components/common/DetailPrimitives"
import { SessionHistory } from "@/components/common/SessionHistory"
import { formatDate } from "@/lib/format"
import { getStatusLabel } from "@/utils/statusColors"

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-fg/10 bg-surface px-3 py-2">
      <p className="text-[11px] text-fg-muted">{label}</p>
      <p className="mt-0.5 truncate text-sm font-medium tabular-nums text-fg">{value}</p>
    </div>
  )
}

/**
 * What this practitioner has actually delivered.
 *
 * The totals come from the server, not from the length of the recent list: a
 * page of twenty says nothing about a practitioner with eighty sessions. The
 * organisation split follows each session's own stored affiliation, so a
 * practitioner who changes firms keeps their past delivery where it happened.
 */
export function ProviderDeliveryPanel({ providerId }: { providerId: string }) {
  const stats = useQuery({
    queryKey: ["providers", providerId, "delivery-stats"],
    queryFn: () => providersApi.getDeliveryStats(providerId),
  })

  const contexts = Object.entries(stats.data?.by_delivery_context ?? {})
  const organisations = stats.data?.by_organisation ?? []

  return (
    <div className="space-y-5">
      {stats.isPending ? (
        <p className="text-sm text-fg-muted">Loading delivery record…</p>
      ) : stats.isError ? (
        <p className="text-sm text-danger-fg" role="alert">
          Could not load the delivery record.
        </p>
      ) : (
        <>
          <div className="grid gap-2 sm:grid-cols-3">
            <Stat label="Sessions delivered" value={stats.data.total_sessions.toLocaleString()} />
            <Stat label="First session" value={formatDate(stats.data.first_session_at)} />
            <Stat label="Last session" value={formatDate(stats.data.last_session_at)} />
          </div>

          {stats.data.total_sessions > 0 ? (
            <div className="grid gap-5 sm:grid-cols-2">
              <RailSection title="Delivered as">
                <ul className="space-y-1">
                  {contexts.map(([context, count]) => (
                    <li key={context} className="flex items-baseline justify-between gap-2 text-xs">
                      <span className="text-fg">{getStatusLabel(context)}</span>
                      <span className="tabular-nums text-fg-muted">{count}</span>
                    </li>
                  ))}
                </ul>
                <p className="text-[11px] text-fg-subtle">
                  Unknown is historical: imported delivery whose context nobody recorded.
                </p>
              </RailSection>

              <RailSection title="Through organisations">
                {organisations.length === 0 ? (
                  <p className="text-xs text-fg-muted">
                    No session was delivered through an organisation.
                  </p>
                ) : (
                  <ul className="space-y-1">
                    {organisations.map((entry) => (
                      <li
                        key={entry.organisation_id}
                        className="flex items-baseline justify-between gap-2 text-xs"
                      >
                        <Link
                          to="/provider-organisations/$organisationId"
                          params={{ organisationId: entry.organisation_id }}
                          className="truncate text-primary hover:underline"
                        >
                          {entry.organisation_name}
                        </Link>
                        <span className="tabular-nums text-fg-muted">{entry.session_count}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </RailSection>
            </div>
          ) : null}
        </>
      )}

      <SessionHistory providerId={providerId} />
    </div>
  )
}
