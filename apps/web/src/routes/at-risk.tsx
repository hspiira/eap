import { createFileRoute, redirect } from "@tanstack/react-router"

export const Route = createFileRoute("/at-risk")({
  beforeLoad: () => {
    throw redirect({ to: "/me", search: { view: "at-risk" as const } })
  },
  component: () => null,
})
