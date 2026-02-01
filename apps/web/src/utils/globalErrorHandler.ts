/**
 * Global Error Handler
 * Handles unhandled errors and promise rejections
 */

import { getErrorMessage } from './errorHandler'

/**
 * Initialize global error handlers
 */
export function setupGlobalErrorHandlers() {
  // Handle unhandled errors
  window.addEventListener('error', (event) => {
    console.error('Unhandled error:', event.error)
    // In production, you might want to send this to an error reporting service
  })

  // Handle unhandled promise rejections
  window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled promise rejection:', event.reason)
    // In production, you might want to send this to an error reporting service
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
