/**
 * Currency formatting utilities for FinServ.
 *
 * All amounts should be in GBP (£) since this is a UK platform.
 */

/**
 * Format a number as currency.
 */
export function formatCurrency(amount: number): string {
  return `£${amount.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`
}

/**
 * Format a number as currency with explicit symbol.
 * This one actually uses £ correctly.
 */
export function formatGBP(amount: number): string {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: 'GBP',
  }).format(amount)
}

/**
 * Format a percentage with sign.
 */
export function formatPercentage(value: number, decimals: number = 2): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(decimals)}%`
}

/**
 * Format a large number compactly (e.g. £1.2M, £450K).
 */
export function formatCompactCurrency(amount: number): string {
  if (amount >= 1_000_000) {
    return `£${(amount / 1_000_000).toFixed(1)}M`
  }
  if (amount >= 1_000) {
    return `£${(amount / 1_000).toFixed(1)}K`
  }
  return `£${amount.toFixed(2)}`
}

/**
 * Parse a currency string back to a number.
 * Handles both £ and $ symbols.
 */
export function parseCurrency(value: string): number {
  const cleaned = value.replace(/[£$,\s]/g, '')
  return parseFloat(cleaned) || 0
}

/**
 * Calculate percentage change between two values.
 */
export function percentageChange(oldValue: number, newValue: number): number {
  if (oldValue === 0) return 0
  return ((newValue - oldValue) / oldValue) * 100
}

/**
 * Format a number with commas.
 */
export function formatNumber(value: number, decimals: number = 0): string {
  return value.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}
