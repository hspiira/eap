import { useEffect,useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft,Check } from 'lucide-react'

import { authApi } from '@/api/endpoints/auth'

export const Route = createFileRoute('/auth/set-password')({
  component: SetPasswordPage,
  validateSearch: (search: Record<string, unknown>) => ({
    token: typeof search.token === 'string' ? search.token : '',
    tenant_code: typeof search.tenant_code === 'string' ? search.tenant_code : '',
  }),
})

const SET_PASSWORD_GENERIC_ERROR =
  'Please check your password and try again. Use at least 8 characters and make sure both fields match.'
const SET_PASSWORD_LINK_ERROR =
  'Invalid or expired link. Request a new link from your administrator.'

function getSetPasswordErrorMessage(error: unknown): string {
  const err = error as { detail?: string | Array<{ loc?: unknown[]; msg?: string }> }
  const detail = err?.detail
  if (detail == null) return SET_PASSWORD_LINK_ERROR

  if (Array.isArray(detail)) {
    const hasPasswordField = detail.some(
      (d) =>
        Array.isArray(d.loc) &&
        d.loc.some((x) => String(x).toLowerCase().includes('password'))
    )
    if (hasPasswordField) return SET_PASSWORD_GENERIC_ERROR
    return SET_PASSWORD_LINK_ERROR
  }

  const s = String(detail).toLowerCase()
  if (
    s.includes('password') ||
    s.includes('body.') ||
    s.includes('validation') ||
    s.includes('at least 8')
  ) {
    return SET_PASSWORD_GENERIC_ERROR
  }
  return SET_PASSWORD_LINK_ERROR
}

function SetPasswordPage() {
  const navigate = useNavigate()
  const { token, tenant_code } = Route.useSearch()
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!token) setError(SET_PASSWORD_LINK_ERROR)
  }, [token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!token) return
    const p = password.trim()
    const pc = passwordConfirm.trim()
    if (p.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    if (p !== pc) {
      setError('Passwords do not match.')
      return
    }
    setLoading(true)
    try {
      await authApi.setInitialPassword({
        token,
        password: p,
        password_confirm: pc,
      })
      setSuccess(true)
    } catch (err) {
      setError(getSetPasswordErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  const goToLogin = () => {
    navigate({
      to: '/auth/login',
      search: { tenant_code: tenant_code || '', email: '' },
    })
  }

  if (success) {
    return (
      <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
          <p className="text-white/70">Password set</p>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-none bg-natural/20 flex items-center justify-center shrink-0">
            <Check className="w-5 h-5 text-natural" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">You can now log in</h2>
            <p className="text-white/70 text-sm">Use your admin email and your new password to sign in.</p>
          </div>
        </div>
        <button
          type="button"
          onClick={goToLogin}
          className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors"
        >
          Go to Sign in
        </button>
        <div className="mt-6 text-center">
          <Link to="/" className="text-white/80 hover:text-white text-sm inline-flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  if (!token) {
    return (
      <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
          <p className="text-white/70">Invalid link</p>
        </div>
        <p className="text-white/80 mb-6">{error}</p>
        <Link
          to="/auth/login"
          search={{ tenant_code: '', email: '' }}
          className="block w-full py-3 bg-[#D0B5B3] hover:bg-[#c0a5a3] text-white font-semibold rounded-none transition-colors text-center"
        >
          Go to Sign in
        </Link>
      </div>
    )
  }

  return (
    <div className="bg-black/20 backdrop-blur-xl p-8 rounded-none border border-white/5">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Evexía</h1>
        <p className="text-white/70">Set your password</p>
      </div>
      <p className="text-white/80 text-sm mb-6 text-center">
        Choose a password for your admin account (min 8 characters).
      </p>

      {error && (
        <div className="mb-4 p-3 bg-[#D0B5B3]/20 border border-[#D0B5B3]/30 text-white text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="password" className="block text-white/90 text-sm font-medium mb-1">
            Password *
          </label>
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            placeholder="••••••••"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
          />
        </div>
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="text-white/70 hover:text-natural text-sm"
        >
          {showPassword ? 'Hide' : 'Show'} password
        </button>
        <div>
          <label htmlFor="password_confirm" className="block text-white/90 text-sm font-medium mb-1">
            Confirm password *
          </label>
          <input
            id="password_confirm"
            name="password_confirm"
            type="password"
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
            required
            minLength={8}
            placeholder="••••••••"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 bg-natural hover:bg-natural-dark text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Setting password...' : 'Set password'}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link to="/" className="text-white/80 hover:text-white text-sm inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </div>
  )
}
