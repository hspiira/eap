import { createFileRoute, Navigate } from "@tanstack/react-router"

export const Route = createFileRoute("/persons/")({
  component: PersonsCompatibilityRedirect,
})

function PersonsCompatibilityRedirect() {
  return <Navigate to="/providers" replace />
}
