/**
 * Create User - redirects to Settings > Users (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'
import { requireAuthBeforeLoad } from '@/lib/route-auth'

export const Route = createFileRoute('/users/new')({
  beforeLoad: () => {
    requireAuthBeforeLoad()
    throw redirect({ to: '/settings', search: { tab: 'users' }, replace: true })
  },
  component: () => null,
})
