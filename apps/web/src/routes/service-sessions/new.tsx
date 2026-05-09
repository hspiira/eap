import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/service-sessions/new")({
  component: ServiceSessionNewRedirect,
})

function ServiceSessionNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/service-sessions", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
