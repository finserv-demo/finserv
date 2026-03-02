/**
 * Tests for date formatting utilities.
 *
 * Documents the UTC vs BST bug — dates are displayed in UTC
 * instead of the user's local timezone.
 */

import { describe, it, expect } from 'vitest'
import { formatDate, formatDateTime, relativeTime, getCurrentTaxYear, isCurrentTaxYear, parseUKDate } from '../utils/dates'

describe('formatDate', () => {
  it('formats a date in dd/mm/yyyy format', () => {
    const result = formatDate('2025-03-15T10:00:00Z')
    expect(result).toBe('15/03/2025')
  })

  it('uses UTC (BUG: should use Europe/London timezone)', () => {
    // During BST (last Sunday of March to last Sunday of October),
    // UTC and London time differ by 1 hour.
    // A time of 23:30 UTC on June 15 is actually 00:30 BST on June 16 in London.
    // This test documents that we incorrectly show June 15 instead of June 16.
    const result = formatDate('2025-06-15T23:30:00Z')
    // BUG: should be 16/06/2025 in BST
    expect(result).toBe('15/06/2025')
  })
})

describe('formatDateTime', () => {
  it('formats date with time', () => {
    const result = formatDateTime('2025-03-15T14:30:00Z')
    expect(result).toBe('15/03/2025 14:30')
  })
})

describe('relativeTime', () => {
  it('shows "just now" for very recent times', () => {
    const now = new Date().toISOString()
    expect(relativeTime(now)).toBe('just now')
  })
})

describe('getCurrentTaxYear', () => {
  it('returns a tax year string in YYYY/YY format', () => {
    const result = getCurrentTaxYear()
    expect(result).toMatch(/^\d{4}\/\d{2}$/)
  })
})

describe('isCurrentTaxYear', () => {
  it('returns true for recent dates', () => {
    const recentDate = new Date()
    recentDate.setDate(recentDate.getDate() - 5)
    expect(isCurrentTaxYear(recentDate.toISOString())).toBe(true)
  })
})

describe('parseUKDate', () => {
  it('parses dd/mm/yyyy format', () => {
    const result = parseUKDate('25/12/2025')
    expect(result).not.toBeNull()
    expect(result!.getDate()).toBe(25)
    expect(result!.getMonth()).toBe(11) // December = 11
    expect(result!.getFullYear()).toBe(2025)
  })

  it('returns null for invalid format', () => {
    expect(parseUKDate('not-a-date')).toBeNull()
  })

  it('returns null for impossible dates', () => {
    expect(parseUKDate('31/02/2025')).toBeNull() // Feb 31 doesn't exist
  })
})
