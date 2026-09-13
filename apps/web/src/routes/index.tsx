import { createFileRoute } from "@tanstack/react-router"

import { DashboardMain } from "@/components/DashboardMain"
import { LandingPage } from "@/components/landing/LandingPage"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/")({
  component: HomePage,
})

function HomePage() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="grid min-h-svh w-full place-items-center bg-bg text-fg">
        <p className="text-sm text-fg-muted">Loading…</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <LandingPage />
  }

  return <DashboardMain />
}
