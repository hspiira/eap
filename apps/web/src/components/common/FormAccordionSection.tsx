/**
 * Form Accordion Section
 * Collapsible optional form section with + / − icon toggle.
 */

import { useState } from 'react'
import { Plus, Minus } from 'lucide-react'

export interface FormAccordionSectionProps {
  title: string
  children: React.ReactNode
  /** Initially expanded */
  defaultOpen?: boolean
  className?: string
}

export function FormAccordionSection({
  title,
  children,
  defaultOpen = false,
  className = '',
}: FormAccordionSectionProps) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div className={className}>
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between py-2 text-left text-sm font-semibold text-text hover:text-primary transition-colors rounded-none"
      >
        <span>{title}</span>
        {open ? (
          <Minus size={16} className="flex-shrink-0 text-text" aria-hidden />
        ) : (
          <Plus size={16} className="flex-shrink-0 text-text" aria-hidden />
        )}
      </button>
      {open && <div className="pb-2 space-y-2">{children}</div>}
    </div>
  )
}
