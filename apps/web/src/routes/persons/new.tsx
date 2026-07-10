import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/persons/new")({
  component: PersonNewRedirect,
})

function PersonNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/persons", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
