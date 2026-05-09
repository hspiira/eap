import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/engagements/new")({
  component: EngagementNewRedirect,
})

function EngagementNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/engagements", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
