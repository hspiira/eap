/**
 * Create Client - redirects to Clients list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/clients/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/clients', replace: true })
  },
  component: () => null,
})
