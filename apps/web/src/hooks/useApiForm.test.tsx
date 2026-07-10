import { act, renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { z } from 'zod'

import { useApiForm } from '@/hooks/useApiForm'
import { TestProviders } from '@/test/utils'
import { ApiError } from '@/types/api'

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  age: z.number().int().min(0, 'Age must be ≥ 0'),
})

type Values = z.infer<typeof schema>

function setup(onSubmit: (values: Values) => Promise<void> | void, options: { successToast?: string; errorToast?: boolean } = {}) {
  return renderHook(
    () =>
      useApiForm<Values>({
        schema,
        defaultValues: { name: '', age: 0 },
        onSubmit,
        ...options,
      }),
    { wrapper: TestProviders },
  )
}

describe('useApiForm — validation', () => {
  it('runs Zod validation and surfaces field errors on submit', async () => {
    const onSubmit = vi.fn()
    const { result } = setup(onSubmit)

    await act(async () => {
      await result.current.submit()
    })

    expect(onSubmit).not.toHaveBeenCalled()
    expect(result.current.formState.errors.name?.message).toBe('Name is required')
  })

  it('calls onSubmit with parsed values when valid', async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined)
    const { result } = setup(onSubmit)

    act(() => {
      result.current.setValue('name', 'Ada')
      result.current.setValue('age', 33)
    })
    await act(async () => {
      await result.current.submit()
    })

    expect(onSubmit).toHaveBeenCalledWith({ name: 'Ada', age: 33 })
  })
})

describe('useApiForm — server error mapping', () => {
  it('maps ApiError.fieldErrors to setError per field', async () => {
    const onSubmit = vi.fn().mockRejectedValue(
      new ApiError('Bad fields', 'VALIDATION', 422, { name: 'Already taken', age: 'Out of range' }),
    )
    const { result } = setup(onSubmit, { errorToast: false })

    act(() => {
      result.current.setValue('name', 'X')
      result.current.setValue('age', 1)
    })
    await act(async () => {
      await result.current.submit()
    })

    await waitFor(() => {
      expect(result.current.formState.errors.name?.message).toBe('Already taken')
      expect(result.current.formState.errors.age?.message).toBe('Out of range')
    })
    expect(result.current.serverError).toBeUndefined()
  })

  it('falls back to root.serverError when no fieldErrors', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new ApiError('Boom', 'CONFLICT', 409))
    const { result } = setup(onSubmit, { errorToast: false })

    act(() => {
      result.current.setValue('name', 'X')
      result.current.setValue('age', 1)
    })
    await act(async () => {
      await result.current.submit()
    })

    await waitFor(() => {
      expect(result.current.serverError).toBe('Boom')
    })
  })

  it('uses defaultErrorMessage for non-ApiError throws', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error('plain throw'))
    const { result } = setup(onSubmit, { errorToast: false })

    act(() => {
      result.current.setValue('name', 'X')
      result.current.setValue('age', 1)
    })
    await act(async () => {
      await result.current.submit()
    })

    await waitFor(() => {
      expect(result.current.serverError).toBe('plain throw')
    })
  })

  it('clears prior root.serverError on retry', async () => {
    const onSubmit = vi
      .fn()
      .mockRejectedValueOnce(new ApiError('first', 'X', 500))
      .mockResolvedValueOnce(undefined)
    const { result } = setup(onSubmit, { errorToast: false })

    act(() => {
      result.current.setValue('name', 'X')
      result.current.setValue('age', 1)
    })
    await act(async () => {
      await result.current.submit()
    })
    await waitFor(() => expect(result.current.serverError).toBeTruthy())

    await act(async () => {
      await result.current.submit()
    })
    await waitFor(() => expect(result.current.serverError).toBeUndefined())
  })
})

describe('useApiForm — submission state', () => {
  it('formState.isSubmitting flips during the call', async () => {
    let resolve: () => void = () => {}
    const onSubmit = vi.fn(
      () =>
        new Promise<void>((res) => {
          resolve = res
        }),
    )
    const { result } = setup(onSubmit)

    act(() => {
      result.current.setValue('name', 'X')
      result.current.setValue('age', 1)
    })

    let submitPromise: Promise<void>
    act(() => {
      submitPromise = result.current.submit()
    })
    await waitFor(() => expect(result.current.formState.isSubmitting).toBe(true))

    await act(async () => {
      resolve()
      await submitPromise
    })
    expect(result.current.formState.isSubmitting).toBe(false)
  })
})
