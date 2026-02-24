/**
 * Create Contract - redirects to Contracts list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/contracts/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/contracts', replace: true })
  },
  component: () => null,
})
