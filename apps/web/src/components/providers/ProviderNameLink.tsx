import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { providersApi } from "@/api/endpoints/providers"
import { entityDetailKey } from "@/lib/queries"

/**
 * A practitioner's name, resolved from their id.
 *
 * Affiliation and session responses carry the practitioner id without a name,
 * so the name comes from a separate cached detail query.
 */
export function ProviderNameLink({ providerId }: { providerId: string }) {
  const query = useQuery({
    queryKey: entityDetailKey("providers", providerId),
    queryFn: () => providersApi.getById(providerId),
    staleTime: 5 * 60_000,
  })

  const label = query.data && (query.data.formal_name || query.data.display_name)

  return (
    <Link
      to="/providers/$providerId"
      params={{ providerId }}
      className="text-sm font-medium text-primary hover:underline"
    >
      {label ?? (query.isPending ? "Loading…" : providerId)}
    </Link>
  )
}
