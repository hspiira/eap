/**
 * Create Service Assignment - redirects to Service Assignments list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/service-assignments/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/service-assignments', replace: true })
  },
  component: () => null,
})
