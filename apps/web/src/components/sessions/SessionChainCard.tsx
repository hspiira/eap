/**
 * A session's place in the chain of care around it.
 *
 * Laid out like the industry tree: what came before sits above, the session
 * being read is the highlighted middle, and what came after is indented below
 * against a rule. A chain of appointments and a hierarchy of industries are
 * the same shape to the eye, so they are the same shape on screen.
 *
 * One hop each way, because that is all the data can honestly show: there is
 * no container holding a whole course of care, and walking further would mean
 * a query per step. See decision 7 in docs/design/REALTIME_SESSION_CAPTURE.md.
 */

import { useQuery } from "@tanstack/react-query"

import { ChevronRight, CornerDownRight } from "lucide-react"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { Button } from "@/components/ui/button"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"
import type { ServiceSession } from "@/types/entities/delivery"

type ChainSession = Pick<
  ServiceSession,
  "id" | "scheduled_at" | "session_number" | "service_name"
> & { service_name?: string | null }

interface Props {
  session: ChainSession
  onSelectSession?: (id: string) => void
}

function nodeLabel(session: ChainSession): string {
  const ordinal = session.session_number ? `Session ${session.session_number}` : "Session"
  return `${ordinal} · ${formatDateTime(session.scheduled_at)}`
}

function ChainNode({
  session,
  kind,
  onSelect,
}: {
  session: ChainSession
  kind: "previous" | "current" | "following"
  onSelect?: (id: string) => void
}) {
  const Icon = kind === "previous" ? CornerDownRight : ChevronRight
  const interactive = kind !== "current" && Boolean(onSelect)
  const inner = (
    <span
      className={cn(
        "flex w-full items-center gap-1.5",
        kind === "current" ? "font-medium text-primary" : "text-fg",
      )}
    >
      <Icon
        className={cn("size-3.5 shrink-0", kind === "current" ? "text-primary" : "text-fg-subtle")}
      />
      <span className="truncate">{nodeLabel(session)}</span>
      {session.service_name ? (
        <span className="truncate text-[11px] text-fg-muted">{session.service_name}</span>
      ) : null}
    </span>
  )
  if (!interactive) return inner
  return (
    <Button
      type="button"
      variant="ghost"
      onClick={() => onSelect?.(session.id)}
      className="-mx-1 h-auto w-[calc(100%+0.5rem)] justify-start rounded-sm px-1 py-0.5 hover:bg-surface-hover hover:[&_span]:text-primary"
      aria-label={`Open ${nodeLabel(session)}`}
    >
      {inner}
    </Button>
  )
}

export function SessionChainCard({ session, onSelectSession }: Props) {
  const { data, isPending } = useQuery({
    queryKey: ["session-chain", session.id],
    queryFn: () => serviceSessionsApi.chain(session.id),
    staleTime: 30_000,
  })

  if (isPending || !data) return null
  const previous = data.previous as ChainSession | null
  const following = (data.following ?? []) as ChainSession[]

  if (!previous && following.length === 0) {
    return (
      <p className="text-xs text-fg-muted">
        Not linked to another session. A follow-up booked from here will appear in this chain.
      </p>
    )
  }

  return (
    <ul className="space-y-1 text-sm">
      {previous ? (
        <li>
          <ChainNode session={previous} kind="previous" onSelect={onSelectSession} />
        </li>
      ) : null}
      <li className={cn(previous && "ml-3 border-l border-fg/10 pl-3")}>
        <ChainNode session={session} kind="current" />
        {following.length > 0 ? (
          <ul className="mt-1 space-y-1">
            {following.map((next) => (
              <li key={next.id} className="ml-3 border-l border-fg/10 pl-3">
                <ChainNode session={next} kind="following" onSelect={onSelectSession} />
              </li>
            ))}
          </ul>
        ) : null}
      </li>
    </ul>
  )
}
