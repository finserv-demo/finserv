/**
 * Risk assessment questionnaire component.
 *
 * Fetches the questionnaire from the risk engine and submits answers
 * to calculate the user's risk profile.
 */

import React, { useState, useEffect } from 'react'

interface Option {
  value: string
  label: string
  score: number
}

interface Question {
  id: string
  text: string
  type: string
  options: Option[]
}

interface Questionnaire {
  id: string
  title: string
  description: string
  questions: Question[]
}

interface RiskResult {
  profile: {
    user_id: string
    score: number
    risk_level: string
    calculated_at: string
  }
  breakdown: Array<{
    question_id: string
    question: string
    answer: string
    score: number
  }>
  recommended_allocation: {
    risk_level: string
    allocation: Record<string, number>
    total_pct: number
  }
}

function RiskQuestionnaire() {
  const [questionnaire, setQuestionnaire] = useState<Questionnaire | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [result, setResult] = useState<RiskResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchQuestionnaire()
  }, [])

  async function fetchQuestionnaire() {
    try {
      const response = await fetch('/api/risk/questionnaire')
      if (!response.ok) throw new Error('Failed to fetch questionnaire')
      const data = await response.json()
      setQuestionnaire(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  async function handleSubmit() {
    if (!questionnaire) return

    setSubmitting(true)
    setError(null)

    try {
      const response = await fetch('/api/risk/questionnaire/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: 'user_001',
          answers,
        }),
      })

      if (!response.ok) throw new Error('Failed to submit questionnaire')
      const data: RiskResult = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="loading">Loading questionnaire...</div>
  if (error) return <div className="error-text">Error: {error}</div>

  if (result) {
    return (
      <div className="card">
        <h2 className="card-title">Your Risk Profile</h2>

        <div className="stat-grid" style={{ marginTop: '1rem' }}>
          <div className="stat-card">
            <div className="stat-label">Risk Score</div>
            <div className="stat-value">{result.profile.score}/10</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Risk Level</div>
            <div className="stat-value" style={{ textTransform: 'capitalize' }}>
              {result.profile.risk_level}
            </div>
          </div>
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <h3 style={{ fontSize: '0.875rem', fontWeight: 600, marginBottom: '0.75rem' }}>
            Recommended Allocation
          </h3>
          {Object.entries(result.recommended_allocation.allocation).map(([asset, pct]) => (
            <div key={asset} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.25rem 0' }}>
              <span style={{ fontSize: '0.875rem', textTransform: 'capitalize' }}>
                {asset.replace(/_/g, ' ')}
              </span>
              <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{pct}%</span>
            </div>
          ))}
        </div>

        <button
          className="btn btn-secondary"
          style={{ marginTop: '1rem' }}
          onClick={() => {
            setResult(null)
            setAnswers({})
          }}
        >
          Retake Questionnaire
        </button>
      </div>
    )
  }

  if (!questionnaire) return null

  const allAnswered = questionnaire.questions.every((q) => answers[q.id])

  return (
    <div className="card">
      <h2 className="card-title">{questionnaire.title}</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
        {questionnaire.description}
      </p>

      {questionnaire.questions.map((question, index) => (
        <div key={question.id} style={{ marginBottom: '1.5rem' }}>
          <p style={{ fontWeight: 500, marginBottom: '0.5rem' }}>
            {index + 1}. {question.text}
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {question.options.map((option) => (
              <label
                key={option.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.5rem',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  background: answers[question.id] === option.value ? '#ebf8ff' : 'transparent',
                }}
              >
                <input
                  type="radio"
                  name={question.id}
                  value={option.value}
                  checked={answers[question.id] === option.value}
                  onChange={() =>
                    setAnswers((prev) => ({ ...prev, [question.id]: option.value }))
                  }
                />
                <span style={{ fontSize: '0.875rem' }}>{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      ))}

      <button
        className="btn btn-primary"
        onClick={handleSubmit}
        disabled={!allAnswered || submitting}
      >
        {submitting ? 'Calculating...' : 'Calculate Risk Profile'}
      </button>

      {!allAnswered && (
        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
          Please answer all {questionnaire.questions.length} questions to continue.
        </p>
      )}
    </div>
  )
}

export default RiskQuestionnaire
