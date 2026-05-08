import { createFileRoute } from "@tanstack/react-router"

import { AppLayout } from "@/components/AppLayout"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/documents")({
  component: DocumentsRoute,
})

function DocumentsRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <div className="p-8 text-ink">Loading…</div>
  if (!isAuthenticated) return null
  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-xl font-semibold text-ink">Documents</h1>
        <p className="mt-2 text-ink/80">Documents — module coming next.</p>
      </div>
    </AppLayout>
  )
}
