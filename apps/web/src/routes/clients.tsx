import { createFileRoute, Outlet } from "@tanstack/react-router"
import { useAuthStore } from "@/store/slices/authSlice"
import { AppLayout } from "@/components/AppLayout"

export const Route = createFileRoute("/clients")({
  component: ClientsLayout,
})

function ClientsLayout() {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!isAuthenticated) return null
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  )
}
