/**
 * Industries List - redirects to Settings > Industries (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/industries/')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/settings', search: { tab: 'industries' }, replace: true })
  },
  component: () => null,
})
