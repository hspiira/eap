import { createFileRoute, Outlet } from "@tanstack/react-router"
import { useAuth } from "@/contexts/AuthContext"
import { AppLayout } from "@/components/AppLayout"

export const Route = createFileRoute("/services")({
  component: ServicesLayout,
})

function ServicesLayout() {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!isAuthenticated) return null
  return <AppLayout><Outlet /></AppLayout>
}
