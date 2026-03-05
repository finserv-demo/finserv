/**
 * Transaction history table with pagination and sorting.
 *
 * BUG: When user changes the sort column, the page number should
 * reset to 1, but it doesn't. The current page is maintained,
 * which can show stale or incorrect data after re-sorting.
 */

import React, { useState, useEffect } from 'react'
import { formatCurrency } from '../utils/currency'
import { formatDateTime } from '../utils/dates'

interface Transaction {
  id: string
  portfolio_id: string
  symbol: string
  transaction_type: string
  quantity: number
  price: number
  total_amount: number
  currency: string
  executed_at: string
  settled: boolean
}

interface TransactionsResponse {
  portfolio_id: string
  transactions: Transaction[]
  page: number
  per_page: number
  total: number
}

function TransactionTable() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [total, setTotal] = useState(0)
  const [sortBy, setSortBy] = useState('executed_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const perPage = 20

  useEffect(() => {
    fetchTransactions()
  }, [page, sortBy, sortOrder])

  async function fetchTransactions() {
    setLoading(true)
    try {
      const response = await fetch(
        `/api/portfolio/portfolio/pf_001/transactions?page=${page}&per_page=${perPage}&sort_by=${sortBy}&sort_order=${sortOrder}`
      )
      if (!response.ok) throw new Error('Failed to fetch transactions')
      const data: TransactionsResponse = await response.json()
      setTransactions(data.transactions)
      setTotal(data.total)
    } catch (err) {
      console.error('Failed to fetch transactions:', err)
    } finally {
      setLoading(false)
    }
  }

  function handleSort(column: string) {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortBy(column)
      setSortOrder('desc')
    }
    // BUG: page number should reset to 1 when sort changes
    // but we're not calling setPage(1) here
  }

  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="card-title">Transaction History</h2>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          {total} transactions
        </span>
      </div>

      {loading ? (
        <div className="loading">Loading transactions...</div>
      ) : (
        <>
          <table>
            <thead>
              <tr>
                <th
                  onClick={() => handleSort('executed_at')}
                  style={{ cursor: 'pointer' }}
                >
                  Date {sortBy === 'executed_at' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th
                  onClick={() => handleSort('symbol')}
                  style={{ cursor: 'pointer' }}
                >
                  Symbol {sortBy === 'symbol' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th>Type</th>
                <th
                  onClick={() => handleSort('quantity')}
                  style={{ cursor: 'pointer' }}
                >
                  Quantity {sortBy === 'quantity' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th>Price</th>
                <th
                  onClick={() => handleSort('total_amount')}
                  style={{ cursor: 'pointer' }}
                >
                  Total {sortBy === 'total_amount' ? (sortOrder === 'asc' ? '↑' : '↓') : ''}
                </th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr key={txn.id}>
                  <td>{formatDateTime(txn.executed_at)}</td>
                  <td style={{ fontWeight: 600 }}>{txn.symbol}</td>
                  <td>
                    <span
                      style={{
                        padding: '0.125rem 0.5rem',
                        borderRadius: '12px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        background: txn.transaction_type === 'BUY' ? '#c6f6d5' : '#fed7d7',
                        color: txn.transaction_type === 'BUY' ? '#22543d' : '#742a2a',
                      }}
                    >
                      {txn.transaction_type}
                    </span>
                  </td>
                  <td>{txn.quantity}</td>
                  <td>{formatCurrency(txn.price)}</td>
                  <td style={{ fontWeight: 500 }}>{formatCurrency(txn.total_amount)}</td>
                  <td>{txn.settled ? 'Settled' : 'Pending'}</td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                    No transactions found
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
              <button
                className="btn btn-secondary"
                disabled={page === 1}
                onClick={() => setPage(page - 1)}
              >
                Previous
              </button>
              <span style={{ padding: '0.5rem', fontSize: '0.875rem' }}>
                Page {page} of {totalPages}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page === totalPages}
                onClick={() => setPage(page + 1)}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default TransactionTable
