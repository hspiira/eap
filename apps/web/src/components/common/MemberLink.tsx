import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { membersApi } from "@/api/endpoints/members"
import { memberLabel } from "@/lib/display"

export function MemberLink({ memberId }: { memberId: string }) {
  const query = useQuery({
    queryKey: ["members", "detail", memberId],
    queryFn: () => membersApi.getById(memberId),
  })
  return (
    <Link
      to="/members/$memberId"
      params={{ memberId }}
      className="text-sm text-primary hover:underline"
    >
      {query.data
        ? memberLabel(query.data)
        : query.isPending
          ? "Loading member…"
          : "Member unavailable"}
    </Link>
  )
}
