import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/care-callbacks/new")({
  component: CampaignNewRedirect,
})

function CampaignNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/care-callbacks", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
