/**
 * Create Document - redirects to Documents list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/documents/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/documents', replace: true })
  },
  component: () => null,
})
