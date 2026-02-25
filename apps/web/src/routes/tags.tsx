import { createFileRoute } from "@tanstack/react-router"
import { useAuth } from "@/contexts/AuthContext"
import { AppLayout } from "@/components/AppLayout"

export const Route = createFileRoute("/tags")({
  component: TagsRoute,
})

function TagsRoute() {
  const { isAuthenticated, isLoading } = useAuth()
  if (isLoading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!isAuthenticated) return null
  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-xl font-semibold text-[#5A626A]">Client Tags</h1>
        <p className="mt-2 text-[#5A626A]/80">Tags — module coming next.</p>
      </div>
    </AppLayout>
  )
}
