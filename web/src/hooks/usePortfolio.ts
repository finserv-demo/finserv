/**
 * Portfolio-specific hooks.
 */

import { useApi } from './useApi'

interface Holding {
  symbol: string
  name: string
  quantity: number
  current_price: number
  value: number
  cost_basis: number
  gain_loss: number
  gain_loss_pct: number
  currency: string
}

interface PortfolioValue {
  portfolio_id: string
  total_value: number
  holdings: Holding[]
  currency: string
  calculated_at: string
}

interface PortfolioDrift {
  portfolio_id: string
  total_drift_pct: number
  holdings_drift: Record<string, number>
  calculated_at: string
}

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

export function usePortfolioValue(portfolioId: string) {
  return useApi<PortfolioValue>(`/portfolio/portfolio/${portfolioId}/value`)
}

export function usePortfolioDrift(portfolioId: string) {
  return useApi<PortfolioDrift>(`/portfolio/portfolio/${portfolioId}/drift`)
}

export function useTransactions(portfolioId: string, page: number = 1) {
  return useApi<TransactionsResponse>(
    `/portfolio/portfolio/${portfolioId}/transactions?page=${page}&per_page=20`
  )
}
