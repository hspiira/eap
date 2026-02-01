/**
 * Session Timeout Manager Component
 * Manages session timeout and shows warning modal
 */

import { ReactNode } from 'react'
import { useSessionTimeout } from '@/hooks/useSessionTimeout'
import { SessionTimeoutWarning } from './SessionTimeoutWarning'
import { useAuth } from '@/contexts/AuthContext'

interface SessionTimeoutManagerProps {
  children: ReactNode
}

export function SessionTimeoutManager({ children }: SessionTimeoutManagerProps) {
  const { showWarning, timeRemaining, extendSession } = useSessionTimeout()
  const { logout } = useAuth()

  const handleExtend = () => {
    extendSession()
  }

  const handleLogout = () => {
    logout()
  }

  return (
    <>
      {children}
      {showWarning && timeRemaining !== null && (
        <SessionTimeoutWarning
          timeRemaining={timeRemaining}
          onExtend={handleExtend}
          onLogout={handleLogout}
        />
      )}
    </>
  )
}
