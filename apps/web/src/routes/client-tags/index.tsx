/**
 * Client Tags List - redirects to Settings > Client tags (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/client-tags/')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/settings', search: { tab: 'client-tags' }, replace: true })
  },
  component: () => null,
})
