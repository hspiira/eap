import { useEffect, useState } from 'react'

/**
 * Returns `value` delayed by `ms`. Useful for debouncing input into a query key.
 */
export function useDebouncedValue<T>(value: T, ms = 300): T {
  const [debounced, setDebounced] = useState(value)

  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(id)
  }, [value, ms])

  return debounced
}
