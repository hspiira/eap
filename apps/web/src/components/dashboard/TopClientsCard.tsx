/**
 * Top clients by delivered sessions: name, bar and value share one row, so
 * the card reads as a bar chart with labels rather than a stacked list.
 */

import { Link } from "@tanstack/react-router"
import { Building2 } from "lucide-react"

import type { ClientSessions } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardEmptyState, CardStat } from "./CardBar"

interface TopClientsCardProps {
  clients: ReadonlyArray<ClientSessions>
  loading?: boolean
}

export function TopClientsCard({ clients, loading }: TopClientsCardProps) {
  const max = Math.max(...clients.map((c) => c.total), 1)
  const total = clients.reduce((sum, c) => sum + c.total, 0)
  return (
    <Card className="flex h-full flex-col rounded-md">
      <CardBar title="Top clients">
        {clients.length > 0 ? <CardStat value={total.toLocaleString()} label="sessions" /> : null}
      </CardBar>
      <CardContent className="flex-1 p-3">
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : clients.length === 0 ? (
          <CardEmptyState
            icon={Building2}
            title="No sessions yet"
            description="Client rankings will appear once sessions are logged in this window."
          />
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

/**
 * Bars are scaled to the longest one but stop short of the full row, so the
 * value that follows always has somewhere to sit without clipping.
 */
const BAR_MAX_WIDTH = 88

function ClientRow({ client, max }: { client: ClientSessions; max: number }) {
  return (
    <Link
      to="/clients/$clientId"
      params={{ clientId: client.client_id }}
      className="group grid grid-cols-[7rem_1fr] items-center gap-3 rounded-md py-0.5 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring sm:grid-cols-[9rem_1fr]"
      aria-label={`${client.client_name}: ${client.total} sessions`}
    >
      <span className="truncate text-sm text-fg group-hover:text-primary">
        {client.client_name}
      </span>
      <span className="flex items-center gap-2">
        <span
          className="h-7 rounded-sm bg-chart-1 transition-[width]"
          style={{ width: `${Math.max((client.total / max) * BAR_MAX_WIDTH, 1)}%` }}
        />
        <span className="text-sm font-medium tabular-nums text-fg">
          {client.total.toLocaleString()}
        </span>
      </span>
    </Link>
  )
}
