import { useState, useCallback } from 'react'

export interface UseModalReturn {
  isOpen: boolean
  loading: boolean
  open: () => void
  close: () => void
  setLoading: (value: boolean) => void
}

/**
 * Reduces boilerplate for modal open/close and loading state.
 * close() no-ops when loading is true so the modal cannot be dismissed during submit.
 */
export function useModal(initialOpen = false): UseModalReturn {
  const [isOpen, setIsOpen] = useState(initialOpen)
  const [loading, setLoading] = useState(false)

  const open = useCallback(() => setIsOpen(true), [])
  const close = useCallback(() => {
    if (!loading) setIsOpen(false)
  }, [loading])

  return {
    isOpen,
    loading,
    open,
    close,
    setLoading,
  }
}
