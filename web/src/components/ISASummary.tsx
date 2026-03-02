/**
 * ISA Summary component — shows ISA allowance usage and contribution form.
 */

import React, { useState, useEffect } from 'react'
import { formatCurrency, formatGBP } from '../utils/currency'

interface ISAData {
  user_id: string
  current_tax_year: string
  contributions_ytd: number
  remaining_allowance: number
  annual_allowance: number
  total_accounts: number
  accounts: Array<{
    id: string
    tax_year: string
    contributions_ytd: number
    annual_allowance: number
  }>
}

function ISASummary() {
  const [isa, setISA] = useState<ISAData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [contributionAmount, setContributionAmount] = useState('')
  const [contributing, setContributing] = useState(false)
  const [contributionResult, setContributionResult] = useState<string | null>(null)

  useEffect(() => {
    fetchISAData()
  }, [])

  async function fetchISAData() {
    try {
      const response = await fetch('/api/tax/isa/summary/user_001')
      if (!response.ok) throw new Error('Failed to fetch ISA data')
      const data = await response.json()
      setISA(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  async function handleContribute() {
    const amount = parseFloat(contributionAmount)
    if (isNaN(amount) || amount <= 0) {
      setContributionResult('Please enter a valid amount')
      return
    }

    setContributing(true)
    setContributionResult(null)

    try {
      const response = await fetch('/api/tax/isa/contribute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: 'user_001', amount }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Contribution failed')
      }

      setContributionResult(`Successfully contributed ${formatGBP(amount)}`)
      setContributionAmount('')
      fetchISAData() // Refresh data
    } catch (err) {
      setContributionResult(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setContributing(false)
    }
  }

  if (loading) return <div className="loading">Loading ISA data...</div>
  if (error) return <div className="error-text">Error: {error}</div>
  if (!isa) return null

  const usedPct = isa.annual_allowance > 0
    ? (isa.contributions_ytd / isa.annual_allowance) * 100
    : 0

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">ISA Summary</h2>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Tax Year: {isa.current_tax_year}
        </span>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Contributed YTD</div>
          {/* Uses formatGBP (correct £ symbol) */}
          <div className="stat-value">{formatGBP(isa.contributions_ytd)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Remaining Allowance</div>
          <div className="stat-value">{formatGBP(isa.remaining_allowance)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Annual Allowance</div>
          <div className="stat-value">{formatGBP(isa.annual_allowance)}</div>
        </div>
      </div>

      {/* Progress bar */}
      <div style={{ marginTop: '1.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Allowance Used</span>
          <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>{usedPct.toFixed(1)}%</span>
        </div>
        <div style={{ height: '12px', background: 'var(--border)', borderRadius: '6px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${Math.min(100, usedPct)}%`,
              background: usedPct > 90 ? 'var(--danger)' : usedPct > 75 ? 'var(--warning)' : 'var(--accent)',
              borderRadius: '6px',
              transition: 'width 0.3s ease',
            }}
          />
        </div>
      </div>

      {/* Contribution form */}
      <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem' }}>
          Make a Contribution
        </h3>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
            <input
              type="number"
              className="form-input"
              placeholder="Amount (£)"
              value={contributionAmount}
              onChange={(e) => setContributionAmount(e.target.value)}
              min="0"
              step="100"
            />
          </div>
          <button
            className="btn btn-primary"
            onClick={handleContribute}
            disabled={contributing}
          >
            {contributing ? 'Processing...' : 'Contribute'}
          </button>
        </div>
        {contributionResult && (
          <p style={{
            fontSize: '0.75rem',
            marginTop: '0.5rem',
            color: contributionResult.includes('Successfully') ? 'var(--accent)' : 'var(--danger)',
          }}>
            {contributionResult}
          </p>
        )}
      </div>

      {/* Historical accounts */}
      {isa.accounts.length > 1 && (
        <div style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.5rem' }}>
            Previous Tax Years
          </h3>
          {isa.accounts
            .filter((a) => a.tax_year !== isa.current_tax_year)
            .map((account) => (
              <div
                key={account.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  padding: '0.5rem 0',
                  borderBottom: '1px solid var(--border)',
                  fontSize: '0.875rem',
                }}
              >
                <span>{account.tax_year}</span>
                <span>{formatGBP(account.contributions_ytd)} contributed</span>
              </div>
            ))}
        </div>
      )}
    </div>
  )
}

export default ISASummary
