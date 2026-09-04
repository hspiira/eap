import * as React from "react"

import { Link } from "@tanstack/react-router"

export interface TrailItem {
  label: string
  /** Route path. Rendered as a link when present, plain text otherwise. */
  to?: string
  search?: Record<string, unknown>
}

interface PageShellProps {
  icon?: React.ElementType
  /** Ancestors above the heading. Items carrying `to` are links. */
  trail?: TrailItem[]
  /** Dot-separated trail, kept for pages not yet moved to `trail`. */
  breadcrumb?: string
  /** The page heading. Taken from the last breadcrumb segment when omitted. */
  title?: string
  actions?: React.ReactNode
  menu?: React.ReactNode
  children?: React.ReactNode
}

/** Splits a dot-separated breadcrumb into its ancestors and its leaf. */
function splitBreadcrumb(breadcrumb: string): { trail: TrailItem[]; title: string } {
  const parts = breadcrumb
    .split(/[·>]/)
    .map((part) => part.trim())
    .filter(Boolean)
  return {
    trail: parts.slice(0, -1).map((label) => ({ label })),
    title: parts[parts.length - 1] ?? "",
  }
}

export function PageShell({
  icon: Icon,
  trail,
  breadcrumb,
  title,
  actions,
  menu,
  children,
}: PageShellProps) {
  const derived = breadcrumb ? splitBreadcrumb(breadcrumb) : null
  const items = trail ?? derived?.trail ?? []
  const heading = title ?? derived?.title ?? ""

  return (
    <div className="flex h-full min-h-0 flex-1 flex-col bg-bg">
      <div className="flex shrink-0 items-start gap-2 border-b border-fg/15 bg-surface py-1.5 pl-3 pr-2">
        <div className="min-w-0 flex-1">
          {items.length > 0 ? (
            <nav aria-label="Breadcrumb">
              <ol className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-fg-muted">
                {items.map((item, index) => (
                  <li key={`${item.label}-${index}`} className="flex items-center gap-1">
                    {index > 0 ? <span aria-hidden>/</span> : null}
                    {item.to ? (
                      <Link
                        to={item.to}
                        search={item.search}
                        className="truncate hover:text-fg hover:underline"
                      >
                        {item.label}
                      </Link>
                    ) : (
                      <span className="truncate">{item.label}</span>
                    )}
                  </li>
                ))}
              </ol>
            </nav>
          ) : null}
          <div className="flex min-w-0 items-center gap-1.5">
            {Icon ? <Icon className="size-3.5 shrink-0 text-fg/60" /> : null}
            <h1 className="min-w-0 truncate text-sm font-semibold text-fg">{heading}</h1>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5 pt-0.5">
          {actions}
          {menu}
        </div>
      </div>
      {children}
    </div>
  )
}
