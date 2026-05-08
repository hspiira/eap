import { createFileRoute } from "@tanstack/react-router"
import { Link } from "@tanstack/react-router"

import { AppLayout } from "@/components/AppLayout"
import { AtRiskPage } from "@/components/AtRiskPage"
import { useAuthStore } from "@/store/slices/authSlice"

export const Route = createFileRoute("/at-risk")({
  component: AtRiskRoute,
})

function AtRiskRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div
        className="min-h-svh w-full flex items-center justify-center bg-surface text-fg"
        style={{ minHeight: "100dvh" }}
      >
        <p>Loading...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-svh w-full flex flex-col items-center justify-center gap-4 bg-surface">
        <p className="text-fg">Sign in to view At Risk.</p>
        <Link to="/auth/login" className="text-primary hover:underline">
          Sign in
        </Link>
      </div>
    )
  }

  return (
    <AppLayout>
      <AtRiskPage />
    </AppLayout>
  )
}
