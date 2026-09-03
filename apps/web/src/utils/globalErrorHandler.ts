/**
 * Global Error Handler
 * Handles unhandled errors and promise rejections.
 * In production, only a safe message is logged to avoid leaking sensitive data.
 */

const isProd = typeof import.meta !== 'undefined' && import.meta.env?.PROD

/**
 * Initialize global error handlers
 */
export function setupGlobalErrorHandlers() {
  window.addEventListener('error', (event) => {
    if (isProd) {
      console.error('Unhandled error')
    } else {
      console.error('Unhandled error:', event.error)
    }
  })

  window.addEventListener('unhandledrejection', (event) => {
    if (isProd) {
      console.error('Unhandled promise rejection')
    } else {
      console.error('Unhandled promise rejection:', event.reason)
    }
  })
}

/**
 * Format error for logging
 */
export function formatErrorForLogging(error: unknown): string {
  if (error instanceof Error) {
    return `${error.name}: ${error.message}\n${error.stack || ''}`
  }
  return String(error)
}
