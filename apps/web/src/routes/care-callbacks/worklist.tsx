import { createFileRoute, Outlet } from "@tanstack/react-router"

export const Route = createFileRoute("/care-callbacks/worklist")({
  component: () => <Outlet />,
})
