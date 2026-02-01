/**
 * Form Validation Utilities
 * Common validation functions and Zod schemas
 */

import { z } from 'zod'

/**
 * Common validation schemas
 */
export const validators = {
  // Email validation
  email: z.string().email('Invalid email address').min(1, 'Email is required'),

  // Password validation
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),

  // Required string
  requiredString: (minLength = 1, maxLength?: number) => {
    let schema = z.string().min(minLength, `Must be at least ${minLength} characters`)
    if (maxLength) {
      schema = schema.max(maxLength, `Must be no more than ${maxLength} characters`)
    }
    return schema
  },

  // Optional string
  optionalString: (maxLength?: number) => {
    let schema = z.string().optional()
    if (maxLength) {
      schema = z.string().max(maxLength, `Must be no more than ${maxLength} characters`).optional()
    }
    return schema
  },

  // URL validation
  url: z.string().url('Invalid URL').optional().or(z.literal('')),

  // Phone number (basic validation)
  phone: z
    .string()
    .regex(/^[\d\s\-\+\(\)]+$/, 'Invalid phone number format')
    .optional()
    .or(z.literal('')),

  // Date validation
  date: z.string().min(1, 'Date is required'),

  // Optional date
  optionalDate: z.string().optional().or(z.literal('')),

  // Number validation
  number: (min?: number, max?: number) => {
    let schema = z.coerce.number()
    if (min !== undefined) {
      schema = schema.min(min, `Must be at least ${min}`)
    }
    if (max !== undefined) {
      schema = schema.max(max, `Must be no more than ${max}`)
    }
    return schema
  },

  // Positive number
  positiveNumber: z.coerce.number().positive('Must be a positive number'),

  // Non-negative number
  nonNegativeNumber: z.coerce.number().nonnegative('Must be zero or greater'),

  // Boolean
  boolean: z.boolean(),

  // Enum validation
  enum: <T extends z.ZodEnum<any>>(enumSchema: T) => enumSchema,

  // Tenant code validation (3-15 lowercase alphanumeric with hyphens)
  tenantCode: z
    .string()
    .min(3, 'Tenant code must be at least 3 characters')
    .max(15, 'Tenant code must be no more than 15 characters')
    .regex(/^[a-z0-9-]+$/, 'Tenant code can only contain lowercase letters, numbers, and hyphens')
    .refine((val) => !val.startsWith('-') && !val.endsWith('-'), {
      message: 'Tenant code cannot start or end with a hyphen',
    }),

  // CUID validation (for IDs)
  cuid: z.string().min(1, 'ID is required'),

  // Optional CUID
  optionalCuid: z.string().optional(),

  // ISO 8601 date string
  isoDate: z.string().datetime('Invalid date format'),

  // Optional ISO 8601 date string
  optionalIsoDate: z.string().datetime('Invalid date format').optional().or(z.literal('')),
}

/**
 * Common validation error messages
 */
export const validationMessages = {
  required: 'This field is required',
  email: 'Please enter a valid email address',
  minLength: (min: number) => `Must be at least ${min} characters`,
  maxLength: (max: number) => `Must be no more than ${max} characters`,
  min: (min: number) => `Must be at least ${min}`,
  max: (max: number) => `Must be no more than ${max}`,
  pattern: 'Invalid format',
  url: 'Please enter a valid URL',
  phone: 'Please enter a valid phone number',
}

/**
 * Helper to get error message from Zod error
 */
export function getZodErrorMessage(error: z.ZodError | null | undefined): string | undefined {
  if (!error || error.errors.length === 0) {
    return undefined
  }
  return error.errors[0].message
}

/**
 * Helper to get field error from form errors
 */
export function getFieldError(
  errors: Record<string, any>,
  fieldName: string
): string | undefined {
  const error = errors[fieldName]
  if (!error) {
    return undefined
  }
  return error.message || error
}
