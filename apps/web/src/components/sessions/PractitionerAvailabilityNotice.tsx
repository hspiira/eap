/**
 * Whether the chosen practitioner is already spoken for at the chosen time.
 *
 * Asked as soon as a practitioner, service and time are all present, so a
 * clash is seen while the choice is still being made rather than as a 409
 * after the form is submitted.
 *
 * It reports only what the platform can see: a booking held in this system.
 * An externally affiliated practitioner keeps their own diary, so "free" here
 * means "nothing booked here", and the notice says so rather than implying
 * the platform knows their day. See "Decision 6" in
 * docs/design/REALTIME_SESSION_CAPTURE.md.
 */

import { useQuery } from "@tanstack/react-query"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { formatDateTime } from "@/lib/format"

interface Props {
  providerId: string
  serviceId: string
  scheduledAt: string
}

function isReady({ providerId, serviceId, scheduledAt }: Props): boolean {
  return Boolean(providerId && serviceId && scheduledAt && !Number.isNaN(Date.parse(scheduledAt)))
}

export function PractitionerAvailabilityNotice(props: Props) {
  const { providerId, serviceId, scheduledAt } = props
  const ready = isReady(props)
  const at = ready ? new Date(scheduledAt).toISOString() : ""

  const { data, isPending } = useQuery({
    queryKey: ["session-availability", providerId, serviceId, at],
    queryFn: () =>
      serviceSessionsApi.availability({
        at,
        service_id: serviceId,
        provider_id: [providerId],
      }),
    enabled: ready,
    staleTime: 30_000,
  })

  if (!ready || isPending || !data) return null
  const entry = data.items.find((item) => item.provider_id === providerId)
  if (!entry) return null

  if (entry.available) {
    return (
      <p className="text-xs text-fg-muted">
        No other booking for this practitioner over the {data.assumed_minutes} minutes from this
        time. Their own diary is not visible here.
      </p>
    )
  }
  return (
    <div
      role="alert"
      className="border border-warning/30 bg-warning-soft px-3 py-2 text-sm text-warning-fg"
    >
      <p className="font-medium">This practitioner is already booked at this time.</p>
      <p className="mt-0.5">
        {entry.clashing_scheduled_at
          ? `Their other session starts ${formatDateTime(entry.clashing_scheduled_at)}.`
          : "Another session of theirs overlaps this slot."}{" "}
        Pick a different practitioner or time.
      </p>
    </div>
  )
}
