/**
 * Portfolio allocation chart component.
 *
 * Shows current vs target allocation as a simple bar chart.
 */

import React, { useState, useEffect } from 'react'

interface DriftData {
  portfolio_id: string
  total_drift_pct: number
  holdings_drift: Record<string, number>
  calculated_at: string
}

const COLORS = ['#1a365d', '#2b6cb0', '#38a169', '#d69e2e', '#e53e3e', '#805ad5']

function PortfolioChart() {
  const [drift, setDrift] = useState<DriftData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDrift()
  }, [])

  async function fetchDrift() {
    try {
      const response = await fetch('/api/portfolio/portfolio/pf_001/drift')
      if (!response.ok) throw new Error('Failed to fetch drift data')
      const data = await response.json()
      setDrift(data)
    } catch (err) {
      console.error('Failed to fetch drift:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">Loading allocation data...</div>
  if (!drift) return null

  const holdings = Object.entries(drift.holdings_drift)

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Portfolio Allocation Drift</h2>
        <span
          className={`stat-change ${drift.total_drift_pct > 5 ? 'negative' : 'positive'}`}
          style={{ fontSize: '0.875rem' }}
        >
          Total drift: {drift.total_drift_pct.toFixed(1)}%
        </span>
      </div>

      <div style={{ marginTop: '1rem' }}>
        {holdings.map(([symbol, driftPct], index) => (
          <div key={symbol} style={{ marginBottom: '0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{symbol}</span>
              <span
                className={driftPct >= 0 ? 'positive' : 'negative'}
                style={{ fontSize: '0.875rem' }}
              >
                {driftPct >= 0 ? '+' : ''}{driftPct.toFixed(1)}%
              </span>
            </div>
            <div
              style={{
                height: '8px',
                background: 'var(--border)',
                borderRadius: '4px',
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, Math.abs(driftPct) * 5 + 50)}%`,
                  background: COLORS[index % COLORS.length],
                  borderRadius: '4px',
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: '1rem', textAlign: 'center' }}>
        <button className="btn btn-primary" onClick={() => alert('Rebalance triggered!')}>
          Rebalance Now
        </button>
      </div>
    </div>
  )
}

export default PortfolioChart
