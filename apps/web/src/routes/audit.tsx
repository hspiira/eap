import { createFileRoute } from "@tanstack/react-router"
import { ClipboardCheck } from "lucide-react"

import { AppLayout } from "@/components/AppLayout"
import { EmptyState } from "@/components/common/EmptyState"

export const Route = createFileRoute("/audit")({
  component: AuditRoute,
})

function AuditRoute() {
  return (
    <AppLayout>
      <EmptyState
        icon={ClipboardCheck}
        title="Audit logs coming soon"
        description="Full tamper-evident audit trail for all platform actions. This module is in active development."
      />
    </AppLayout>
  )
}
