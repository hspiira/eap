/**
 * Create Contact - redirects to Contacts list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/contacts/new')({
  beforeLoad: () => {
    throw redirect({ to: '/contacts' })
  },
  component: () => null,
})
