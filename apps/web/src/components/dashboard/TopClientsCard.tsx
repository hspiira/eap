/**
 * Top clients by delivered sessions: name, bar and value share one row, so
 * the card reads as a bar chart with labels rather than a stacked list.
 */

import { Link } from "@tanstack/react-router"

import type { ClientSessions } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardStat } from "./CardBar"

interface TopClientsCardProps {
  clients: ReadonlyArray<ClientSessions>
  loading?: boolean
}

export function TopClientsCard({ clients, loading }: TopClientsCardProps) {
  const max = Math.max(...clients.map((c) => c.total), 1)
  const total = clients.reduce((sum, c) => sum + c.total, 0)
  return (
    <Card className="rounded-md">
      <CardBar title="Top clients">
        {clients.length > 0 ? <CardStat value={total.toLocaleString()} label="sessions" /> : null}
      </CardBar>
      <CardContent className="p-3">
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : clients.length === 0 ? (
          <p className="py-6 text-center text-sm text-fg-muted">No sessions in this window.</p>
        ) : (
          <ul className="grid gap-2.5">
            {clients.map((client) => (
              <li key={client.client_id}>
                <ClientRow client={client} max={max} />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function ClientRow({ client, max }: { client: ClientSessions; max: number }) {
  return (
    <Link
      to="/clients/$clientId"
      params={{ clientId: client.client_id }}
      className="group grid grid-cols-[8rem_1fr_2.5rem] items-center gap-3 rounded-md py-0.5 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:grid-cols-[10rem_1fr_2.5rem]"
      aria-label={`${client.client_name}: ${client.total} sessions`}
    >
      <span className="truncate text-sm text-fg group-hover:text-primary">
        {client.client_name}
      </span>
      <span className="h-5 rounded-sm bg-chart-1/10">
        <span
          className="block h-full rounded-sm bg-chart-1 transition-[width]"
          style={{ width: `${Math.max((client.total / max) * 100, 2)}%` }}
        />
      </span>
      <span className="text-right text-sm font-medium tabular-nums text-fg">
        {client.total.toLocaleString()}
      </span>
    </Link>
  )
}
