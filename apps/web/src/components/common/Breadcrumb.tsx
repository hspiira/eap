/**
 * Breadcrumb Component
 * Navigation breadcrumb with design system styling. Uses Link for navigable items.
 */

import { Link } from '@tanstack/react-router'
import { ChevronRight } from 'lucide-react'

export interface BreadcrumbItem {
  label: string
  href?: string
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[]
  className?: string
}

export function Breadcrumb({ items, className = '' }: BreadcrumbProps) {
  if (items.length === 0) return null

  return (
    <nav aria-label="Breadcrumb" className={`flex flex-wrap items-center gap-1 text-sm ${className}`}>
      {items.map((item, index) => {
        const isLast = index === items.length - 1
        const showSeparator = index > 0

        return (
          <span key={index} className="flex items-center gap-1">
            {showSeparator && (
              <ChevronRight
                size={14}
                className="flex-shrink-0 text-text-muted"
                aria-hidden
              />
            )}
            {isLast || !item.href ? (
              <span
                className="text-text font-medium"
                aria-current={isLast ? 'page' : undefined}
              >
                {item.label}
              </span>
            ) : (
              <Link
                to={item.href}
                className="text-text hover:text-primary transition-colors"
              >
                {item.label}
              </Link>
            )}
          </span>
        )
      })}
    </nav>
  )
}
