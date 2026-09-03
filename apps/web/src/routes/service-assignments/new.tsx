import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/service-assignments/new")({
  component: ServiceAssignmentNewRedirect,
})

function ServiceAssignmentNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/service-assignments", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
