/**
 * Create User - redirects to Users list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/users/new')({
  beforeLoad: () => {
    throw redirect({ to: '/users' })
  },
  component: () => null,
})
