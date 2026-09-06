import { createFileRoute, Navigate } from "@tanstack/react-router"

export const Route = createFileRoute("/persons/new")({
  component: PersonNewCompatibilityRedirect,
})

function PersonNewCompatibilityRedirect() {
  return <Navigate to="/members" search={{ new: true }} replace />
}
