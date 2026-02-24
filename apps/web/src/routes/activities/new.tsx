/**
 * Create Activity - redirects to Activities list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/activities/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/activities', replace: true })
  },
  component: () => null,
})
