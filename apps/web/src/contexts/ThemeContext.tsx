import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

const THEME_KEY = 'evexia_theme'

export type ThemePreference = 'light' | 'dark' | 'system'
type EffectiveTheme = 'light' | 'dark'

interface ThemeContextType {
  preference: ThemePreference
  effectiveTheme: EffectiveTheme
  setPreference: (preference: ThemePreference) => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

function getSystemTheme(): EffectiveTheme {
  if (typeof window === 'undefined') return 'light'
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function getStoredPreference(): ThemePreference | null {
  if (typeof window === 'undefined') return null
  const stored = localStorage.getItem(THEME_KEY) as ThemePreference | null
  return stored === 'light' || stored === 'dark' || stored === 'system' ? stored : null
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [preference, setPreferenceState] = useState<ThemePreference>(() => {
    return getStoredPreference() ?? 'system'
  })
  const [systemTheme, setSystemTheme] = useState<EffectiveTheme>(getSystemTheme)

  const effectiveTheme: EffectiveTheme =
    preference === 'system' ? systemTheme : preference

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', effectiveTheme)
  }, [effectiveTheme])

  useEffect(() => {
    if (typeof window === 'undefined') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    if (!mq) return
    const handler = () => setSystemTheme(mq.matches ? 'dark' : 'light')
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])

  const setPreference = (p: ThemePreference) => {
    setPreferenceState(p)
    localStorage.setItem(THEME_KEY, p)
  }

  return (
    <ThemeContext.Provider value={{ preference, effectiveTheme, setPreference }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (ctx === undefined) {
    throw new Error('useTheme must be used within ThemeProvider')
  }
  return ctx
}
