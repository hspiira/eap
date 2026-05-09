import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/services/new")({
  component: ServiceNewRedirect,
})

function ServiceNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/services", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
