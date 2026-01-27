/**
 * useSessionTimeout Hook
 * Manages session timeout based on user inactivity
 */

import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'

const PREFERENCE_KEY = 'evexia_pref_session_timeout'
const WARNING_TIME = 60000 // Show warning 1 minute before timeout

export function useSessionTimeout() {
  const { isAuthenticated, logout } = useAuth()
  const [timeRemaining, setTimeRemaining] = useState<number | null>(null)
  const [showWarning, setShowWarning] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout | null>(null)
  const warningTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastActivityRef = useRef<number>(Date.now())
  const warningShownAtRef = useRef<number | null>(null)

  const getTimeoutMinutes = useCallback(() => {
    if (typeof window === 'undefined') return 30
    const stored = localStorage.getItem(PREFERENCE_KEY)
    return stored ? parseInt(stored, 10) : 30
  }, [])

  const resetTimer = useCallback(() => {
    // Clear existing timers
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    if (warningTimeoutRef.current) {
      clearTimeout(warningTimeoutRef.current)
      warningTimeoutRef.current = null
    }

    if (!isAuthenticated) {
      setShowWarning(false)
      setTimeRemaining(null)
      warningShownAtRef.current = null
      return
    }

    const timeoutMinutes = getTimeoutMinutes()
    const timeoutMs = timeoutMinutes * 60 * 1000
    const warningTime = timeoutMs - WARNING_TIME

    lastActivityRef.current = Date.now()
    setShowWarning(false)
    setTimeRemaining(timeoutMs)

    // Set warning timer
    if (warningTime > 0) {
      warningTimeoutRef.current = setTimeout(() => {
        warningShownAtRef.current = Date.now()
        setShowWarning(true)
        setTimeRemaining(WARNING_TIME)
      }, warningTime)
    }

    // Set logout timer
    timeoutRef.current = setTimeout(() => {
      logout()
    }, timeoutMs)
  }, [isAuthenticated, logout, getTimeoutMinutes])

  const handleActivity = useCallback(() => {
    const now = Date.now()
    // Throttle activity tracking to avoid excessive resets (max once per second)
    if (now - lastActivityRef.current < 1000) {
      return
    }
    resetTimer()
  }, [resetTimer])

  const extendSession = useCallback(() => {
    resetTimer()
  }, [resetTimer])

  // Track user activity
  useEffect(() => {
    if (!isAuthenticated) {
      return
    }

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click']
    
    events.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true })
    })

    // Initialize timer
    resetTimer()

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity)
      })
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      if (warningTimeoutRef.current) {
        clearTimeout(warningTimeoutRef.current)
      }
    }
  }, [isAuthenticated, handleActivity, resetTimer])

  // Update time remaining countdown when warning is shown
  useEffect(() => {
    if (!showWarning || !isAuthenticated || warningShownAtRef.current === null) {
      return
    }

    const interval = setInterval(() => {
      const elapsed = Date.now() - warningShownAtRef.current!
      const remaining = WARNING_TIME - elapsed
      setTimeRemaining(Math.max(0, remaining))
      
      // Auto-logout if time runs out (fallback, main timer should handle this)
      if (remaining <= 0) {
        logout()
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [showWarning, isAuthenticated, logout])

  return {
    showWarning,
    timeRemaining,
    extendSession,
  }
}
