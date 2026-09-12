import { createFileRoute } from "@tanstack/react-router"
import { Users } from "lucide-react"

import { AuthedLayout } from "@/components/common/AuthedLayout"
import { EmptyState } from "@/components/common/EmptyState"

export const Route = createFileRoute("/contacts")({
  component: ContactsRoute,
})

function ContactsRoute() {
  return (
    <AuthedLayout>
      <EmptyState
        icon={Users}
        title="Contacts coming soon"
        description="Unified contact directory across clients and persons. This module is in active development."
      />
    </AuthedLayout>
  )
}
