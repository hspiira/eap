import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/clients/new")({
  component: ClientNewRedirect,
})

function ClientNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/clients", search: { new: "1" }, replace: true })
  }, [navigate])
  return null
}
