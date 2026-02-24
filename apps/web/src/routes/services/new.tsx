/**
 * Create Service - redirects to Services list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/services/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/services', replace: true })
  },
  component: () => null,
})
