/**
 * Tests for currency formatting utilities.
 */

import { describe, it, expect } from 'vitest'
import { formatCurrency, formatGBP, formatPercentage, formatCompactCurrency, parseCurrency, percentageChange } from '../utils/currency'

describe('formatCurrency', () => {
  it('formats basic amounts', () => {
    expect(formatCurrency(1234.56)).toBe('£1,234.56')
  })

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('£0.00')
  })

  it('formats large amounts with commas', () => {
    expect(formatCurrency(1000000)).toBe('£1,000,000.00')
  })
})

describe('formatGBP', () => {
  it('formats correctly with £ symbol', () => {
    const result = formatGBP(1234.56)
    expect(result).toContain('£')
    expect(result).toContain('1,234.56')
  })
})

describe('formatPercentage', () => {
  it('formats positive percentages with + sign', () => {
    expect(formatPercentage(5.25)).toBe('+5.25%')
  })

  it('formats negative percentages', () => {
    expect(formatPercentage(-3.1)).toBe('-3.10%')
  })

  it('formats zero', () => {
    expect(formatPercentage(0)).toBe('+0.00%')
  })
})

describe('formatCompactCurrency', () => {
  it('formats millions with M suffix', () => {
    expect(formatCompactCurrency(1500000)).toBe('£1.5M')
  })

  it('formats thousands with K suffix', () => {
    expect(formatCompactCurrency(45000)).toBe('£45.0K')
  })

  it('formats small amounts normally', () => {
    expect(formatCompactCurrency(123.45)).toBe('£123.45')
  })
})

describe('parseCurrency', () => {
  it('parses £ amounts', () => {
    expect(parseCurrency('£1,234.56')).toBe(1234.56)
  })

  it('parses $ amounts', () => {
    expect(parseCurrency('$1,234.56')).toBe(1234.56)
  })

  it('returns 0 for invalid input', () => {
    expect(parseCurrency('abc')).toBe(0)
  })
})

describe('percentageChange', () => {
  it('calculates positive change', () => {
    expect(percentageChange(100, 110)).toBe(10)
  })

  it('calculates negative change', () => {
    expect(percentageChange(100, 90)).toBe(-10)
  })

  it('returns 0 when old value is 0', () => {
    expect(percentageChange(0, 100)).toBe(0)
  })
})
