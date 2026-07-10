import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/contracts/new")({
  component: ContractNewRedirect,
})

function ContractNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/contracts", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
