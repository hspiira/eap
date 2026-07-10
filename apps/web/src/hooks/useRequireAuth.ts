import { useEffect } from 'react'

import { useNavigate } from '@tanstack/react-router'

import { useAuthStore } from '@/store/slices/authSlice'

export function useRequireAuth() {
  const { isLoading, isAuthenticated } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate({
        to: '/auth/login',
        search: { tenant_code: undefined, email: undefined, redirect: undefined },
        replace: true,
      })
    }
  }, [isLoading, isAuthenticated, navigate])

  return useAuthStore()
}
