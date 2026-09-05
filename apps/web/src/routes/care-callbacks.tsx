import { createFileRoute, Outlet } from "@tanstack/react-router"

import { AppLayout } from "@/components/AppLayout"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/care-callbacks")({
  component: CareCallbacksLayout,
})

function CareCallbacksLayout() {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <div className="p-8 text-fg">Loading…</div>
  if (!isAuthenticated) return null
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  )
}
