import { createFileRoute } from "@tanstack/react-router"
import { FolderOpen } from "lucide-react"

import { AppLayout } from "@/components/AppLayout"
import { EmptyState } from "@/components/common/EmptyState"

export const Route = createFileRoute("/documents")({
  component: DocumentsRoute,
})

function DocumentsRoute() {
  return (
    <AppLayout>
      <EmptyState
        icon={FolderOpen}
        title="Documents coming soon"
        description="Centralised document storage and version management for clients and engagements. This module is in active development."
      />
    </AppLayout>
  )
}
