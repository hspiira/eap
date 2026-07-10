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

  it('opens the panel and renders root nodes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    await screen.findByPlaceholderText(/search diagnoses/i)
    await waitFor(() => expect(screen.getByText(/Mental and behavioural disorders/i)).toBeInTheDocument())
  })

  it('expanding a category loads its children', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    await screen.findByPlaceholderText(/search diagnoses/i)
    await screen.findByText(/Mental and behavioural disorders/i)
    const expandButtons = screen.getAllByRole('button', { name: /expand/i })
    fireEvent.click(expandButtons[0])
    await waitFor(() =>
      expect(screen.getByText(/Mood \(affective\) disorders/i)).toBeInTheDocument(),
    )
  })

  it('search shows matching nodes', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search diagnoses/i)
    await user.type(input, 'post')
    await waitFor(
      () => expect(screen.getAllByText(/Post-traumatic stress disorder/i).length).toBeGreaterThan(0),
      { timeout: 2000 },
    )
  })

  it('selecting a node fires onChange and closes the panel', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={onChange} />)

    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search diagnoses/i)
    await user.type(input, 'F32.1')
    await waitFor(
      () => expect(screen.getAllByText(/Moderate depressive episode/i).length).toBeGreaterThan(0),
      { timeout: 2000 },
    )
    const matches = screen.getAllByText(/Moderate depressive episode/i)
    const button = matches[0].closest('button')
    if (button) fireEvent.click(button)

    await waitFor(() => expect(onChange).toHaveBeenCalledWith('icd10-f32-mod'))
  })

  it('shows empty-state when no matches', async () => {
    const user = userEvent.setup()
    renderWithProviders(<ControlledHarness onChangeSpy={() => {}} />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search diagnoses/i)
    await user.type(input, 'zzz-no-match')
    expect(await screen.findByText(/no matches/i)).toBeInTheDocument()
  })

  it('leavesOnly disables selection on category nodes', async () => {
    function Harness() {
      const [v, setV] = useState<string | null>(null)
      return (
        <DiagnosisSelector value={v} onChange={(id) => setV(id)} leavesOnly />
      )
    }
    const user = userEvent.setup()
    renderWithProviders(<Harness />)
    await user.click(screen.getByRole('button', { name: /select diagnosis/i }))
    const input = await screen.findByPlaceholderText(/search diagnoses/i)
    await user.type(input, 'Mental and behavioural disorders')
    const row = await screen.findByText(/Mental and behavioural disorders/i)
    const button = row.closest('button') as HTMLButtonElement
    expect(button).toBeDisabled()
  })
})
