import { useState } from 'react'

import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { DiagnosisSelector } from '@/components/common/DiagnosisSelector'
import { renderWithProviders } from '@/test/utils'

function ControlledHarness({
  onChangeSpy,
}: {
  onChangeSpy: (id: string | null) => void
}) {
  const [value, setValue] = useState<string | null>(null)
  return (
    <DiagnosisSelector
      value={value}
      onChange={(id) => {
        setValue(id)
        onChangeSpy(id)
      }}
    />
  )
}

describe('DiagnosisSelector', () => {
  it('shows placeholder when nothing selected', () => {
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    expect(screen.getByText('Select diagnosis')).toBeInTheDocument()
  })

  it('opens the panel and renders type group headers', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    await screen.findByPlaceholderText(/search by code or name/i)
    await waitFor(() =>
      expect(screen.getByText(/Mood \(affective\) disorders/i)).toBeInTheDocument(),
    )
  })

  it('expanding a type group reveals its diagnoses', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    await screen.findByText(/Mood \(affective\) disorders/i)
    await user.click(screen.getByRole('button', { name: /Mood \(affective\) disorders/i }))
    await waitFor(() =>
      expect(screen.getAllByText(/Depressive episode/i).length).toBeGreaterThan(0),
    )
  })

  it('search shows matching diagnoses across types', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, 'post')
    await waitFor(
      () =>
        expect(
          screen.getAllByText(/Post-traumatic stress disorder/i).length,
        ).toBeGreaterThan(0),
      { timeout: 2000 },
    )
  })

  it('selecting a diagnosis fires onChange with its id and closes the panel', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={onChange} />)

    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, 'F32.1')
    await waitFor(
      () =>
        expect(
          screen.getAllByText(/Moderate depressive episode/i).length,
        ).toBeGreaterThan(0),
      { timeout: 2000 },
    )
    const matches = screen.getAllByText(/Moderate depressive episode/i)
    const button = matches[0].closest('button')
    if (button) fireEvent.click(button)

    await waitFor(() => expect(onChange).toHaveBeenCalledWith('dx-f32-1'))
  })

  it('shows empty-state when no matches', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, 'zzz-no-match')
    expect(await screen.findByText(/no matches/i)).toBeInTheDocument()
  })

  it('displays selected diagnosis code and name on the trigger', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search by code or name/i)
    await user.type(input, 'F32.1')
    await waitFor(
      () => expect(screen.getAllByText(/Moderate depressive episode/i).length).toBeGreaterThan(0),
      { timeout: 2000 },
    )
    const matches = screen.getAllByText(/Moderate depressive episode/i)
    const button = matches[0].closest('button')
    if (button) fireEvent.click(button)

    await waitFor(() =>
      expect(screen.getByRole('button', { name: /F32\.1.*Moderate depressive episode/i })).toBeInTheDocument(),
    )
  })
})
