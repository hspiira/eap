import { createFileRoute } from "@tanstack/react-router"
import { Activity } from "lucide-react"

import { AppLayout } from "@/components/AppLayout"
import { EmptyState } from "@/components/common/EmptyState"

export const Route = createFileRoute("/activities")({
  component: ActivitiesRoute,
})

function ActivitiesRoute() {
  return (
    <AppLayout>
      <EmptyState
        icon={Activity}
        title="Activity logs coming soon"
        description="Per-user and per-resource activity stream for operational visibility. This module is in active development."
      />
    </AppLayout>
  )
}
