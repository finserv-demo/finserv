/**
 * Dashboard component — shows portfolio overview stats.
 *
 * BUG: Uses formatCurrency() which shows '$' instead of '£'.
 * Should use formatGBP() instead.
 */

import React, { useState, useEffect } from 'react'
import { formatCurrency, formatPercentage } from '../utils/currency'

interface PortfolioSummary {
  portfolio_id: string
  account_type: string
  total_value: number
  daily_pnl: number
  total_drift_pct: number
  holdings_count: number
  last_rebalanced: string | null
  currency: string
}

interface HoldingValue {
  symbol: string
  name: string
  quantity: number
  current_price: number
  value: number
  cost_basis: number
  gain_loss: number
  gain_loss_pct: number
}

interface PortfolioValue {
  portfolio_id: string
  total_value: number
  holdings: HoldingValue[]
  currency: string
}

function Dashboard() {
  const [portfolio, setPortfolio] = useState<PortfolioValue | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPortfolioData()
  }, [])

  async function fetchPortfolioData() {
    try {
      const response = await fetch('/api/portfolio/portfolio/pf_001/value')
      if (!response.ok) throw new Error('Failed to fetch portfolio data')
      const data = await response.json()
      setPortfolio(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) return <div className="loading">Loading portfolio...</div>
  if (error) return <div className="error-text">Error: {error}</div>
  if (!portfolio) return <div className="loading">No portfolio data</div>

  const totalGainLoss = portfolio.holdings.reduce((sum, h) => sum + h.gain_loss, 0)
  const totalCostBasis = portfolio.holdings.reduce((sum, h) => sum + h.cost_basis, 0)
  const totalGainLossPct = totalCostBasis > 0 ? (totalGainLoss / totalCostBasis) * 100 : 0

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Portfolio Overview</h2>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ISA Account</span>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Total Value</div>
          {/* BUG: formatCurrency shows $ instead of £ */}
          <div className="stat-value">{formatCurrency(portfolio.total_value)}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Gain/Loss</div>
          <div className={`stat-value ${totalGainLoss >= 0 ? 'positive' : 'negative'}`}>
            {formatCurrency(Math.abs(totalGainLoss))}
          </div>
          <div className={`stat-change ${totalGainLoss >= 0 ? 'positive' : 'negative'}`}>
            {formatPercentage(totalGainLossPct)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Holdings</div>
          <div className="stat-value">{portfolio.holdings.length}</div>
        </div>
      </div>

      <div style={{ marginTop: '1.5rem' }}>
        <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem' }}>Holdings</h3>
        <table>
          <thead>
            <tr>
              <th>Symbol</th>
              <th>Name</th>
              <th>Qty</th>
              <th>Price</th>
              <th>Value</th>
              <th>Gain/Loss</th>
            </tr>
          </thead>
          <tbody>
            {portfolio.holdings.map((holding) => (
              <tr key={holding.symbol}>
                <td style={{ fontWeight: 600 }}>{holding.symbol}</td>
                <td>{holding.name}</td>
                <td>{holding.quantity}</td>
                {/* BUG: formatCurrency shows $ */}
                <td>{formatCurrency(holding.current_price)}</td>
                <td>{formatCurrency(holding.value)}</td>
                <td className={holding.gain_loss >= 0 ? 'positive' : 'negative'}>
                  {formatCurrency(Math.abs(holding.gain_loss))} ({formatPercentage(holding.gain_loss_pct)})
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Dashboard
