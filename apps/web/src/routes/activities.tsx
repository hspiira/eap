import { createFileRoute } from "@tanstack/react-router"

import { AppLayout } from "@/components/AppLayout"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/activities")({
  component: ActivitiesRoute,
})

function ActivitiesRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!isAuthenticated) return null
  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-xl font-semibold text-[#5A626A]">Activity Logs</h1>
        <p className="mt-2 text-[#5A626A]/80">Activity logs — module coming next.</p>
      </div>
    </AppLayout>
  )
}
