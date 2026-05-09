import { useEffect, useState } from 'react'

import { useUIStore, type EffectiveTheme } from '@/store/slices/uiSlice'

function getSystemTheme(): EffectiveTheme {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

/**
 * Subscribes to the user's theme preference + system preference, and applies
 * the resulting `data-theme` attribute and `dark` class to `<html>`. Mount once
 * at the route root.
 */
export function useThemeEffect(): EffectiveTheme {
  const preference = useUIStore((s) => s.theme)
  const [systemTheme, setSystemTheme] = useState<EffectiveTheme>(getSystemTheme)
  const effective: EffectiveTheme = preference === 'system' ? systemTheme : preference

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', effective)
    root.classList.toggle('dark', effective === 'dark')
  }, [effective])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    if (!mq) return
    const handler = () => setSystemTheme(mq.matches ? 'dark' : 'light')
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  return effective
}
