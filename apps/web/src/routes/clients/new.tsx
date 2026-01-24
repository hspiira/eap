/**
 * Create Client - redirects to Clients list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/clients/new')({
  beforeLoad: () => {
    throw redirect({ to: '/clients' })
  },
  component: () => null,
})
