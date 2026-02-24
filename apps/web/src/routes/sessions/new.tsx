/**
 * Create Session - redirects to Sessions list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/sessions/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/sessions', replace: true })
  },
  component: () => null,
})
