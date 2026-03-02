import React, { useState } from 'react'
import Dashboard from './components/Dashboard'
import PortfolioChart from './components/PortfolioChart'
import TransactionTable from './components/TransactionTable'
import RiskQuestionnaire from './components/RiskQuestionnaire'
import ISASummary from './components/ISASummary'
import OnboardingForm from './components/OnboardingForm'
import NotificationList from './components/NotificationList'
import './App.css'

type Tab = 'dashboard' | 'transactions' | 'risk' | 'isa' | 'onboarding' | 'notifications'

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('dashboard')

  const tabs: { id: Tab; label: string }[] = [
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'transactions', label: 'Transactions' },
    { id: 'risk', label: 'Risk Profile' },
    { id: 'isa', label: 'ISA' },
    { id: 'onboarding', label: 'Onboarding' },
    { id: 'notifications', label: 'Notifications' },
  ]

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <h1 className="logo">FinServ</h1>
          <span className="tagline">UK Robo-Advisor</span>
        </div>
        <nav className="nav-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <main className="app-main">
        {activeTab === 'dashboard' && (
          <div className="dashboard-layout">
            <Dashboard />
            <PortfolioChart />
          </div>
        )}
        {activeTab === 'transactions' && <TransactionTable />}
        {activeTab === 'risk' && <RiskQuestionnaire />}
        {activeTab === 'isa' && <ISASummary />}
        {activeTab === 'onboarding' && <OnboardingForm />}
        {activeTab === 'notifications' && <NotificationList />}
      </main>

      <footer className="app-footer">
        <p>FinServ Ltd — Authorised and regulated by the FCA (demo)</p>
      </footer>
    </div>
  )
}

export default App
