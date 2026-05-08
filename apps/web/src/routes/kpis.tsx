import { createFileRoute } from "@tanstack/react-router"

import { AppLayout } from "@/components/AppLayout"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/kpis")({
  component: KPIsRoute,
})

function KPIsRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <div className="p-8 text-fg">Loading…</div>
  if (!isAuthenticated) return null
  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-xl font-semibold text-fg">KPIs</h1>
        <p className="mt-2 text-fg/80">KPIs — module coming next.</p>
      </div>
    </AppLayout>
  )
}
