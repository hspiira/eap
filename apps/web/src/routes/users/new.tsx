import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/users/new")({
  component: UserNewRedirect,
})

function UserNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/users", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
