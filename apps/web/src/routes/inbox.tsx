import { createFileRoute, redirect } from "@tanstack/react-router"

/**
 * `/inbox` is a work-in-progress screen reachable from the profile page rather
 * than the main nav; it renders inside `/me`'s layout.
 */
export const Route = createFileRoute("/inbox")({
  beforeLoad: () => {
    throw redirect({ to: "/me", search: { view: "inbox" as const } })
  },
  component: () => null,
})
