/**
 * Create Industry - redirects to Industries list (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/industries/new')({
  beforeLoad: () => {
    throw redirect({ to: '/industries' })
  },
  component: () => null,
})
