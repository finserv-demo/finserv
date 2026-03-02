/**
 * Onboarding form component for new user registration.
 *
 * Collects personal details, NI number, postcode, etc.
 * and submits to the onboarding service for KYC processing.
 */

import React, { useState } from 'react'

interface FormData {
  first_name: string
  last_name: string
  email: string
  phone: string
  postcode: string
  ni_number: string
  date_of_birth: string
}

interface FormErrors {
  [key: string]: string
}

function OnboardingForm() {
  const [formData, setFormData] = useState<FormData>({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    postcode: '',
    ni_number: '',
    date_of_birth: '',
  })
  const [errors, setErrors] = useState<FormErrors>({})
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null)

  function handleChange(field: keyof FormData, value: string) {
    setFormData((prev) => ({ ...prev, [field]: value }))
    // Clear error on change
    if (errors[field]) {
      setErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
    }
  }

  function validateLocally(): boolean {
    const newErrors: FormErrors = {}

    if (!formData.first_name.trim()) newErrors.first_name = 'First name is required'
    if (!formData.last_name.trim()) newErrors.last_name = 'Last name is required'
    if (!formData.email.trim()) newErrors.email = 'Email is required'
    if (!formData.phone.trim()) newErrors.phone = 'Phone number is required'
    if (!formData.postcode.trim()) newErrors.postcode = 'Postcode is required'
    if (!formData.ni_number.trim()) newErrors.ni_number = 'NI number is required'
    if (!formData.date_of_birth) newErrors.date_of_birth = 'Date of birth is required'

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    if (!validateLocally()) return

    setSubmitting(true)
    setResult(null)

    try {
      const response = await fetch('/api/onboarding/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const serverErrors: FormErrors = {}
          errorData.detail.forEach((err: { field: string; message: string }) => {
            serverErrors[err.field] = err.message
          })
          setErrors(serverErrors)
          throw new Error('Validation failed')
        }
        throw new Error(errorData.detail || 'Submission failed')
      }

      const data = await response.json()
      setResult({
        success: true,
        message: `Application submitted! Your reference: ${data.application_id}. KYC review will be completed within 24 hours.`,
      })
    } catch (err) {
      if (!result) {
        setResult({
          success: false,
          message: err instanceof Error ? err.message : 'Unknown error',
        })
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (result?.success) {
    return (
      <div className="card">
        <h2 className="card-title">Application Submitted</h2>
        <p style={{ color: 'var(--accent)', marginTop: '1rem' }}>{result.message}</p>
        <button
          className="btn btn-secondary"
          style={{ marginTop: '1rem' }}
          onClick={() => {
            setResult(null)
            setFormData({
              first_name: '',
              last_name: '',
              email: '',
              phone: '',
              postcode: '',
              ni_number: '',
              date_of_birth: '',
            })
          }}
        >
          Submit Another Application
        </button>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="card-title">Open an Account</h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginBottom: '1.5rem' }}>
        Complete the form below to start your investment journey with FinServ.
      </p>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">First Name</label>
            <input
              className="form-input"
              value={formData.first_name}
              onChange={(e) => handleChange('first_name', e.target.value)}
              placeholder="James"
            />
            {errors.first_name && <div className="error-text">{errors.first_name}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">Last Name</label>
            <input
              className="form-input"
              value={formData.last_name}
              onChange={(e) => handleChange('last_name', e.target.value)}
              placeholder="Smith"
            />
            {errors.last_name && <div className="error-text">{errors.last_name}</div>}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Email</label>
          <input
            type="email"
            className="form-input"
            value={formData.email}
            onChange={(e) => handleChange('email', e.target.value)}
            placeholder="james.smith@example.co.uk"
          />
          {errors.email && <div className="error-text">{errors.email}</div>}
        </div>

        <div className="form-group">
          <label className="form-label">Phone Number</label>
          <input
            className="form-input"
            value={formData.phone}
            onChange={(e) => handleChange('phone', e.target.value)}
            placeholder="07700 900 123"
          />
          {errors.phone && <div className="error-text">{errors.phone}</div>}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div className="form-group">
            <label className="form-label">Postcode</label>
            <input
              className="form-input"
              value={formData.postcode}
              onChange={(e) => handleChange('postcode', e.target.value)}
              placeholder="SW1A 1AA"
            />
            {errors.postcode && <div className="error-text">{errors.postcode}</div>}
          </div>

          <div className="form-group">
            <label className="form-label">National Insurance Number</label>
            <input
              className="form-input"
              value={formData.ni_number}
              onChange={(e) => handleChange('ni_number', e.target.value)}
              placeholder="AB 12 34 56 C"
            />
            {errors.ni_number && <div className="error-text">{errors.ni_number}</div>}
          </div>
        </div>

        <div className="form-group">
          <label className="form-label">Date of Birth</label>
          <input
            type="date"
            className="form-input"
            value={formData.date_of_birth}
            onChange={(e) => handleChange('date_of_birth', e.target.value)}
          />
          {errors.date_of_birth && <div className="error-text">{errors.date_of_birth}</div>}
        </div>

        {result && !result.success && (
          <div className="error-text" style={{ marginBottom: '1rem' }}>{result.message}</div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting}
        >
          {submitting ? 'Submitting...' : 'Submit Application'}
        </button>
      </form>
    </div>
  )
}

export default OnboardingForm
