/**
 * Users List - redirects to Settings > Users (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/users/')({
  beforeLoad: () => {
    throw redirect({ to: '/settings', search: { tab: 'users' }, replace: true })
  },
  component: () => null,
})
