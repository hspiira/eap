import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { providerOrganisationsApi } from "@/api/endpoints/provider-organisations"
import { entityDetailKey } from "@/lib/queries"
import type { ServiceSession } from "@/types/entities"
import { SessionDeliveryContext } from "@/types/enums"

/**
 * How a session was delivered, as recorded.
 *
 * An unknown context is shown as unknown. It means the source evidence does
 * not say, which is not the same as direct delivery, and the two must not be
 * conflated in a session view.
 */
export function SessionDeliveryLabel({ session }: { session: ServiceSession }) {
  const context = session.delivery_context ?? null
  const organisationId = session.provider_organisation_id ?? null

  const organisation = useQuery({
    queryKey: entityDetailKey("provider-organisations", organisationId ?? ""),
    queryFn: () => providerOrganisationsApi.getById(organisationId as string),
    enabled: Boolean(organisationId),
    staleTime: 5 * 60_000,
  })

  if (context === SessionDeliveryContext.DIRECT) {
    return <span className="text-sm text-fg">Direct</span>
  }

  if (context === SessionDeliveryContext.ORGANISATION) {
    if (!organisationId) {
      return (
        <span className="text-sm text-danger-fg">
          Organisation delivery with no organisation recorded
        </span>
      )
    }
    return (
      <Link
        to="/provider-organisations/$organisationId"
        params={{ organisationId }}
        className="text-sm text-primary hover:underline"
      >
        {organisation.data?.name ?? (organisation.isPending ? "Loading…" : organisationId)}
      </Link>
    )
  }

  if (context === SessionDeliveryContext.UNKNOWN) {
    return (
      <span className="text-sm text-fg-muted">
        Unknown. The source record does not say how this session was delivered.
      </span>
    )
  }

  return <span className="text-sm text-fg-subtle">Not recorded</span>
}

/** The stored attribution, shown read-only where it must not be edited. */
export function StoredAttribution({ session }: { session: ServiceSession | null }) {
  if (!session) return null
  return (
    <div className="border border-fg/10 bg-surface px-3 py-2">
      <p className="text-[11px] font-medium tracking-wide text-fg-muted">Delivered through</p>
      <div className="mt-0.5">
        <SessionDeliveryLabel session={session} />
      </div>
      <p className="mt-1.5 text-xs text-fg-muted">
        Attribution is not changed here. Correcting who delivered a session is a separate, audited
        action, so past records keep their meaning.
      </p>
    </div>
  )
}
