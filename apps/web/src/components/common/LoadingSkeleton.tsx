/**
 * Loading Skeleton Component
 * Placeholder components for loading states
 */

export interface LoadingSkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular' | 'table-row' | 'card'
  width?: string | number
  height?: string | number
  lines?: number
  className?: string
}

export function LoadingSkeleton({
  variant = 'rectangular',
  width,
  height,
  lines = 1,
  className = '',
}: LoadingSkeletonProps) {
  const baseClasses = 'bg-safe-light animate-pulse'

  if (variant === 'text') {
    return (
      <div className={className}>
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={`${baseClasses} mb-2`}
            style={{
              width: width || (index === lines - 1 ? '60%' : '100%'),
              height: height || '1rem',
            }}
          />
        ))}
      </div>
    )
  }

  if (variant === 'circular') {
    return (
      <div
        className={`${baseClasses} rounded-none ${className}`}
        style={{
          width: width || height || '40px',
          height: height || width || '40px',
        }}
      />
    )
  }

  if (variant === 'table-row') {
    return (
      <tr className={className}>
        <td colSpan={100} className="p-4">
          <div className="flex items-center gap-4">
            <div className={`${baseClasses} w-10 h-10`} />
            <div className="flex-1 space-y-2">
              <div className={`${baseClasses} h-4 w-3/4`} />
              <div className={`${baseClasses} h-3 w-1/2`} />
            </div>
          </div>
        </td>
      </tr>
    )
  }

  if (variant === 'card') {
    return (
      <div className={`border border-[0.5px] border-safe/30 p-4 ${className}`}>
        <div className={`${baseClasses} h-6 w-3/4 mb-3`} />
        <div className={`${baseClasses} h-4 w-full mb-2`} />
        <div className={`${baseClasses} h-4 w-5/6`} />
      </div>
    )
  }

  // Rectangular (default)
  return (
    <div
      className={`${baseClasses} ${className}`}
      style={{
        width: width || '100%',
        height: height || '1rem',
      }}
    />
  )
}

/**
 * Table Row Skeleton
 * Pre-configured skeleton for table rows
 */
export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }).map((_, index) => (
        <td key={index} className="px-4 py-3">
          <LoadingSkeleton variant="text" lines={1} width="80%" />
        </td>
      ))}
    </tr>
  )
}

/**
 * Card Skeleton
 * Pre-configured skeleton for cards
 */
export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div className="border border-[0.5px] border-safe/30 p-6 bg-white">
      <LoadingSkeleton variant="text" lines={lines} />
    </div>
  )
}
