import { createFileRoute } from "@tanstack/react-router"
import { useAuthStore } from "@/store/slices/authSlice"
import { AppLayout } from "@/components/AppLayout"

export const Route = createFileRoute("/contacts")({
  component: ContactsRoute,
})

function ContactsRoute() {
  const { isAuthenticated, isLoading } = useAuthStore()
  if (isLoading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!isAuthenticated) return null
  return (
    <AppLayout>
      <div className="p-8">
        <h1 className="text-xl font-semibold text-[#5A626A]">Contacts</h1>
        <p className="mt-2 text-[#5A626A]/80">Contacts — module coming next.</p>
      </div>
    </AppLayout>
  )
}
