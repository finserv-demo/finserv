/**
 * Date formatting utilities for FinServ.
 *
 * UK-specific date handling: dd/mm/yyyy format, BST/GMT timezone.
 *
 * BUG: Several functions display dates in UTC instead of the user's
 * local timezone (which should default to Europe/London for UK users).
 */

/**
 * Format a date string for display.
 *
 * BUG: Uses UTC timezone instead of Europe/London.
 * UK users should see dates in BST (summer) or GMT (winter),
 * but this always shows UTC which can be off by 1 hour during BST.
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString)
  // BUG: uses UTC methods instead of locale-aware formatting
  const day = date.getUTCDate().toString().padStart(2, '0')
  const month = (date.getUTCMonth() + 1).toString().padStart(2, '0')
  const year = date.getUTCFullYear()
  return `${day}/${month}/${year}`
}

/**
 * Format a date with time.
 *
 * BUG: Also uses UTC — should use Europe/London timezone.
 */
export function formatDateTime(dateString: string): string {
  const date = new Date(dateString)
  // BUG: UTC instead of local/BST
  const day = date.getUTCDate().toString().padStart(2, '0')
  const month = (date.getUTCMonth() + 1).toString().padStart(2, '0')
  const year = date.getUTCFullYear()
  const hours = date.getUTCHours().toString().padStart(2, '0')
  const minutes = date.getUTCMinutes().toString().padStart(2, '0')
  return `${day}/${month}/${year} ${hours}:${minutes}`
}

/**
 * Get a relative time string (e.g. "2 hours ago", "3 days ago").
 */
export function relativeTime(dateString: string): string {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffSecs = Math.floor(diffMs / 1000)
  const diffMins = Math.floor(diffSecs / 60)
  const diffHours = Math.floor(diffMins / 60)
  const diffDays = Math.floor(diffHours / 24)

  if (diffDays > 30) return formatDate(dateString)
  if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  if (diffMins > 0) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
  return 'just now'
}

/**
 * Get the current UK tax year string.
 * Tax year runs April 6 to April 5.
 */
export function getCurrentTaxYear(): string {
  const now = new Date()
  const month = now.getMonth() + 1
  const day = now.getDate()

  let startYear: number
  if (month > 4 || (month === 4 && day >= 6)) {
    startYear = now.getFullYear()
  } else {
    startYear = now.getFullYear() - 1
  }

  const endYear = (startYear + 1).toString().slice(-2)
  return `${startYear}/${endYear}`
}

/**
 * Check if a date falls in the current UK tax year.
 */
export function isCurrentTaxYear(dateString: string): boolean {
  const date = new Date(dateString)
  const now = new Date()

  // Get tax year boundaries
  const month = now.getMonth() + 1
  const day = now.getDate()

  let taxYearStart: Date
  if (month > 4 || (month === 4 && day >= 6)) {
    taxYearStart = new Date(now.getFullYear(), 3, 6) // April 6 this year
  } else {
    taxYearStart = new Date(now.getFullYear() - 1, 3, 6) // April 6 last year
  }

  return date >= taxYearStart && date <= now
}

/**
 * Format a date for API requests (ISO format).
 */
export function toISODate(date: Date): string {
  return date.toISOString().split('T')[0]
}

/**
 * Parse a UK-format date string (dd/mm/yyyy) to a Date object.
 */
export function parseUKDate(dateString: string): Date | null {
  const parts = dateString.split('/')
  if (parts.length !== 3) return null

  const day = parseInt(parts[0], 10)
  const month = parseInt(parts[1], 10) - 1
  const year = parseInt(parts[2], 10)

  const date = new Date(year, month, day)

  // Validate the date is real
  if (date.getDate() !== day || date.getMonth() !== month) {
    return null
  }

  return date
}
