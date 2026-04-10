import { useState } from 'react'
import { getWinnerLabel } from '../lib/arenaPresentation'


export default function FeedbackPanel({ onSubmit, onReset }) {
  const [rating, setRating] = useState(0)
  const [winner, setWinner] = useState('')
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!rating || submitting) return

    setSubmitting(true)
    setError(null)
    const ok = await onSubmit(rating, comment, winner || null)
    setSubmitting(false)

    if (ok) {
      setSubmitted(true)
      return
    }

    setError('Feedback could not be stored. Please try once more.')
  }

  if (submitted) {
    return (
      <section className="arena-panel">
        <div className="eyebrow">Feedback Stored</div>
        <h3 className="panel-title">Audience Verdict Recorded</h3>
        <p className="text-slate-300 mt-3">
          Your reaction is now part of the debate history.
        </p>
        <button type="button" onClick={onReset} className="arena-btn subtle-btn mt-5 w-full px-4 py-3 sm:w-auto">
          Start Another Debate
        </button>
      </section>
    )
  }

  return (
    <section className="arena-panel">
      <div className="eyebrow">Post-Debate Feedback</div>
      <h3 className="panel-title">How did that verdict land?</h3>

      <form onSubmit={handleSubmit} className="space-y-5 mt-5">
        <div>
          <label className="eyebrow mb-2 block">Who won?</label>
          <div className="grid grid-cols-3 gap-2">
            {['pro', 'tie', 'con'].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setWinner(value)}
                className={`vote-chip ${winner === value ? 'vote-chip-active' : ''}`}
              >
                {getWinnerLabel(value)}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="eyebrow mb-2 block">Rate The Debate</label>
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-5">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setRating(value)}
                className={`rating-chip ${rating >= value ? 'rating-chip-active' : ''}`}
              >
                {value}
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="eyebrow mb-2 block">Your Take</label>
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            rows={4}
            maxLength={500}
            className="arena-input w-full px-4 py-3 resize-none"
            placeholder="What was the turning point? Which side felt sharper?"
          />
        </div>

        {error && <div className="text-sm text-red-300">{error}</div>}

        <div className="flex flex-col gap-3 md:flex-row">
          <button
            type="submit"
            disabled={!rating || submitting}
            className="arena-btn hero-cta w-full px-5 py-3 md:w-auto"
          >
            {submitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
          <button type="button" onClick={onReset} className="arena-btn subtle-btn w-full px-5 py-3 md:w-auto">
            New Debate
          </button>
        </div>
      </form>
    </section>
  )
}
