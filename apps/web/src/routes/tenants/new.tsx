import { useEffect } from 'react'

import { createFileRoute, useNavigate } from '@tanstack/react-router'

export const Route = createFileRoute('/tenants/new')({
  component: TenantNewRedirect,
})

function TenantNewRedirect() {
  const navigate = useNavigate()
  useEffect(() => {
    navigate({
      to: '/tenants',
      search: { new: true, search: undefined, status: undefined },
      replace: true,
    })
  }, [navigate])
  return null
}
