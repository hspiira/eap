/**
 * Client Tags List - redirects to Settings > Client tags (create via modal)
 */

import { createFileRoute, redirect } from '@tanstack/react-router'

export const Route = createFileRoute('/client-tags/')({
  beforeLoad: () => {
    throw redirect({ to: '/settings', search: { tab: 'client-tags' } })
  },
  component: () => null,
})
