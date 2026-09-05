import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/tags/new")({
  component: TagNewRedirect,
})

function TagNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/tags", replace: true })
  }, [navigate])
  return null
}
