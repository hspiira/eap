import { createFileRoute } from "@tanstack/react-router"
import { Users } from "lucide-react"

import { AppLayout } from "@/components/AppLayout"
import { EmptyState } from "@/components/common/EmptyState"

export const Route = createFileRoute("/contacts")({
  component: ContactsRoute,
})

function ContactsRoute() {
  return (
    <AppLayout>
      <EmptyState
        icon={Users}
        title="Contacts coming soon"
        description="Unified contact directory across clients and persons. This module is in active development."
      />
    </AppLayout>
  )
}
