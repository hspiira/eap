import { createFileRoute } from "@tanstack/react-router"
import { useAuth } from "@/contexts/AuthContext"
import { AppLayout } from "@/components/AppLayout"
import { AtRiskPage } from "@/components/AtRiskPage"
import { Link } from "@tanstack/react-router"

export const Route = createFileRoute("/at-risk")({
  component: AtRiskRoute,
})

function AtRiskRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div
        className="min-h-svh w-full flex items-center justify-center bg-[#E6E0D7] text-[#5A626A]"
        style={{ minHeight: "100dvh" }}
      >
        <p>Loading...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-svh w-full flex flex-col items-center justify-center gap-4 bg-[#E6E0D7]">
        <p className="text-[#5A626A]">Sign in to view At Risk.</p>
        <Link to="/auth/login" className="text-natural hover:underline">
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
