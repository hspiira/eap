import type { ReactNode } from 'react'

interface GallerySectionProps {
  id: string
  title: string
  description?: string
  children: ReactNode
}

export function GallerySection({ id, title, description, children }: GallerySectionProps) {
  return (
    <section id={id} className="border-b border-border-subtle py-8 first:pt-4">
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-fg">{title}</h2>
        {description ? (
          <p className="mt-1 text-sm text-fg-muted">{description}</p>
        ) : null}
      </header>
      <div className="grid gap-4">{children}</div>
    </section>
  )
}

interface GallerySpecimenProps {
  label: string
  source?: string
  children: ReactNode
}

export function GallerySpecimen({ label, source, children }: GallerySpecimenProps) {
  return (
    <div className="grid gap-2">
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-fg-muted">
          {label}
        </span>
        {source ? (
          <code className="font-mono text-xs text-fg-subtle">{source}</code>
        ) : null}
      </div>
      <div className="rounded-md border border-border bg-surface p-4">
        {children}
      </div>
    </div>
  )
}
