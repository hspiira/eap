import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

export const Route = createFileRoute("/surveys/new")({
  component: SurveyNewRedirect,
})

function SurveyNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({ to: "/surveys", search: { new: true }, replace: true })
  }, [navigate])
  return null
}
