/**
 * Create User - redirects to Settings > Users (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/users/new')({
  beforeLoad: () => {
    throw redirect({ to: '/settings', search: { tab: 'users' }, replace: true })
  },
  component: () => null,
})
