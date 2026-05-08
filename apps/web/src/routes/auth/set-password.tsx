import { useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Check } from 'lucide-react'
import { z } from 'zod'

import { authApi } from '@/api/endpoints/auth'
import { useApiForm } from '@/hooks/useApiForm'
import { isApiError, isValidationError } from '@/lib/errors'
import { ApiError } from '@/types/api'

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

const setPasswordSchema = z
  .object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    password_confirm: z.string(),
  })
  .refine((d) => d.password === d.password_confirm, {
    path: ['password_confirm'],
    message: 'Passwords do not match',
  })

function SetPasswordPage() {
  const navigate = useNavigate()
  const { token, tenant_code } = Route.useSearch()
  const [showPassword, setShowPassword] = useState(false)
  const [success, setSuccess] = useState(false)

  const { register, formState, submit, serverError } = useApiForm<z.infer<typeof setPasswordSchema>>({
    schema: setPasswordSchema,
    defaultValues: { password: '', password_confirm: '' },
    errorToast: false,
    onSubmit: async (values) => {
      if (!token) {
        throw new ApiError(SET_PASSWORD_LINK_ERROR, 'INVALID_TOKEN', 400)
      }
      try {
        await authApi.setInitialPassword({
          token,
          password: values.password,
          password_confirm: values.password_confirm,
        })
        setSuccess(true)
      } catch (err) {
        if (isValidationError(err)) {
          throw new ApiError(SET_PASSWORD_GENERIC_ERROR, err.code, err.status, {
            password: SET_PASSWORD_GENERIC_ERROR,
          })
        }
        throw new ApiError(
          SET_PASSWORD_LINK_ERROR,
          isApiError(err) ? err.code : 'INVALID_TOKEN',
          isApiError(err) ? err.status : 400,
        )
      }
    },
  })

  const goToLogin = () => {
    navigate({
      to: '/auth/login',
      search: { tenant_code: tenant_code || undefined, email: undefined, redirect: undefined },
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
          <div className="w-10 h-10 rounded-none bg-primary/20 flex items-center justify-center shrink-0">
            <Check className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">You can now log in</h2>
            <p className="text-white/70 text-sm">Use your admin email and your new password to sign in.</p>
          </div>
        </div>
        <button
          type="button"
          onClick={goToLogin}
          className="w-full py-3 bg-primary hover:bg-primary text-white font-semibold rounded-none transition-colors"
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
        <p className="text-white/80 mb-6">{SET_PASSWORD_LINK_ERROR}</p>
        <Link
          to="/auth/login"
          search={{ tenant_code: undefined, email: undefined, redirect: undefined }}
          className="block w-full py-3 bg-danger-soft hover:bg-danger-soft-dark text-white font-semibold rounded-none transition-colors text-center"
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

      {serverError && (
        <div className="mb-4 p-3 bg-danger-soft/20 border border-danger-soft/30 text-white text-sm">
          {serverError}
        </div>
      )}

      <form onSubmit={submit} className="space-y-4" noValidate>
        <div>
          <label htmlFor="password" className="block text-white/90 text-sm font-medium mb-1">
            Password *
          </label>
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
            {...register('password')}
          />
          {formState.errors.password && (
            <p className="mt-1 text-sm text-danger-soft">{formState.errors.password.message as string}</p>
          )}
        </div>
        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="text-white/70 hover:text-primary text-sm"
        >
          {showPassword ? 'Hide' : 'Show'} password
        </button>
        <div>
          <label htmlFor="password_confirm" className="block text-white/90 text-sm font-medium mb-1">
            Confirm password *
          </label>
          <input
            id="password_confirm"
            type="password"
            placeholder="••••••••"
            className="w-full px-4 py-2 bg-white/10 border border-white/20 text-white placeholder:text-white/50 rounded-none focus:outline-none focus:ring-1 focus:ring-white/30"
            {...register('password_confirm')}
          />
          {formState.errors.password_confirm && (
            <p className="mt-1 text-sm text-danger-soft">{formState.errors.password_confirm.message as string}</p>
          )}
        </div>

        <button
          type="submit"
          disabled={formState.isSubmitting}
          className="w-full py-3 bg-primary hover:bg-primary text-white font-semibold rounded-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {formState.isSubmitting ? 'Setting password...' : 'Set password'}
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
