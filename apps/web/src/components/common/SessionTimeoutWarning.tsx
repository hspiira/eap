/**
 * Session Timeout Warning Modal
 * Shows warning before session expires due to inactivity
 */

import { Clock, LogOut } from 'lucide-react'

interface SessionTimeoutWarningProps {
  timeRemaining: number
  onExtend: () => void
  onLogout: () => void
}

export function SessionTimeoutWarning({
  timeRemaining,
  onExtend,
  onLogout,
}: SessionTimeoutWarningProps) {
  const minutes = Math.floor(timeRemaining / 60000)
  const seconds = Math.floor((timeRemaining % 60000) / 1000)
  const formattedTime = `${minutes}:${seconds.toString().padStart(2, '0')}`

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface p-6 rounded-none border border-[0.5px] border-border max-w-md w-full">
        <div className="flex items-start gap-4 mb-4">
          <div className="flex-shrink-0">
            <Clock size={24} className="text-nurturing" />
          </div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-text mb-2">Session Timeout Warning</h2>
            <p className="text-sm text-text-light mb-4">
              Your session will expire due to inactivity in{' '}
              <span className="font-mono font-semibold text-text">{formattedTime}</span>.
            </p>
            <p className="text-xs text-text-light">
              Click "Stay Signed In" to extend your session, or you will be automatically signed out.
            </p>
          </div>
        </div>
        <div className="flex gap-2 justify-end">
          <button
            onClick={onLogout}
            className="px-4 py-2 text-sm border border-[0.5px] border-border text-text hover:bg-surface-hover rounded-none transition-colors flex items-center gap-2"
          >
            <LogOut size={16} />
            Sign Out Now
          </button>
          <button
            onClick={onExtend}
            className="px-4 py-2 text-sm bg-primary hover:bg-primary-hover text-white rounded-none transition-colors"
          >
            Stay Signed In
          </button>
        </div>
      </div>
    </div>
  )
}
