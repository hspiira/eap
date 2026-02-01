/**
 * Empty State Component
 * Displays a message when there's no data to show
 */

import { LucideIcon, Inbox, Search, FileX, Database } from 'lucide-react'

export type EmptyStateVariant = 'default' | 'search' | 'no-results' | 'error' | 'no-data'

export interface EmptyStateProps {
  title?: string
  message?: string
  icon?: LucideIcon
  variant?: EmptyStateVariant
  action?: {
    label: string
    onClick: () => void
  }
  className?: string
}

const defaultConfig: Record<
  EmptyStateVariant,
  { title: string; message: string; icon: typeof Inbox }
> = {
  default: {
    title: 'No items found',
    message: 'There are no items to display at this time.',
    icon: Inbox,
  },
  search: {
    title: 'No search results',
    message: 'Try adjusting your search terms or filters.',
    icon: Search,
  },
  'no-results': {
    title: 'No results found',
    message: 'No items match your current filters.',
    icon: FileX,
  },
  error: {
    title: 'Unable to load data',
    message: 'Something went wrong while loading the data. Please try again.',
    icon: Database,
  },
  'no-data': {
    title: 'No data available',
    message: 'There is no data to display.',
    icon: Inbox,
  },
}

export function EmptyState({
  title,
  message,
  icon: Icon,
  variant = 'default',
  action,
  className = '',
}: EmptyStateProps) {
  const config = defaultConfig[variant]
  const displayTitle = title || config.title
  const displayMessage = message || config.message
  const DisplayIcon = Icon || config.icon

  return (
    <div
      className={`flex flex-col items-center justify-center p-12 text-center bg-surface border border-[0.5px] border-border ${className}`}
    >
      <DisplayIcon size={48} className="text-text-muted mb-4" />
      <h3 className="text-lg font-semibold text-text mb-2">{displayTitle}</h3>
      <p className="text-text-muted mb-6 max-w-md">{displayMessage}</p>
      {action && (
        <button
          onClick={action.onClick}
          className="px-6 py-2 bg-primary hover:bg-primary-hover text-white rounded-none transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  )
}
