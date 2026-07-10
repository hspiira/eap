import { useState } from 'react'

import { createFileRoute, Link, useNavigate } from '@tanstack/react-router'
import { ArrowLeft, Check } from 'lucide-react'
import { z } from 'zod'

import { authApi } from '@/api/endpoints/auth'
import { FormField } from '@/components/common/FormField'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
      <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
          <p className="text-fg-muted">Password set</p>
        </div>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-sm bg-brand-soft flex items-center justify-center shrink-0">
            <Check className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-fg">You can now log in</h2>
            <p className="text-fg-muted text-sm">Use your admin email and your new password to sign in.</p>
          </div>
        </div>
        <Button type="button" onClick={goToLogin} className="w-full">
          Go to Sign in
        </Button>
        <div className="mt-6 text-center">
          <Link to="/" className="text-fg-muted hover:text-fg text-sm inline-flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" />
            Back to Home
          </Link>
        </div>
      </div>
    )
  }

  if (!token) {
    return (
      <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
          <p className="text-fg-muted">Invalid link</p>
        </div>
        <p className="text-fg mb-6">{SET_PASSWORD_LINK_ERROR}</p>
        <Link
          to="/auth/login"
          search={{ tenant_code: undefined, email: undefined, redirect: undefined }}
          className="block w-full py-3 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-sm transition-colors text-center"
        >
          Go to Sign in
        </Link>
      </div>
    )
  }

  return (
    <div className="bg-surface text-fg p-8 rounded-sm border border-border-strong shadow-lg">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-semibold text-primary mb-2">Evexía</h1>
        <p className="text-fg-muted">Set your password</p>
      </div>
      <p className="text-fg-muted text-sm mb-6 text-center">
        Choose a password for your admin account (min 8 characters).
      </p>

      {serverError && (
        <div className="mb-4 p-3 bg-danger-soft border border-danger/30 text-danger-fg text-sm rounded-sm">
          {serverError}
        </div>
      )}

      <form onSubmit={submit} className="space-y-4" noValidate>
        <FormField
          label="Password"
          required
          error={formState.errors.password?.message}
          htmlFor="password"
        >
          <Input
            id="password"
            type={showPassword ? 'text' : 'password'}
            placeholder="••••••••"
            {...register('password')}
          />
        </FormField>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowPassword(!showPassword)}
          className="h-auto p-0 text-fg-muted hover:text-primary text-sm"
        >
          {showPassword ? 'Hide' : 'Show'} password
        </Button>
        <FormField
          label="Confirm password"
          required
          error={formState.errors.password_confirm?.message}
          htmlFor="password_confirm"
        >
          <Input
            id="password_confirm"
            type="password"
            placeholder="••••••••"
            {...register('password_confirm')}
          />
        </FormField>

        <Button
          type="submit"
          disabled={formState.isSubmitting}
          className="w-full"
        >
          {formState.isSubmitting ? 'Setting password...' : 'Set password'}
        </Button>
      </form>

      <div className="mt-6 text-center">
        <Link to="/" className="text-fg-muted hover:text-fg text-sm inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          Back to Home
        </Link>
      </div>
    </div>
  )
}
