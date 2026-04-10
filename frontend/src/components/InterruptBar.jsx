import { useState } from 'react'

import AgentIcon from './AgentIcon'


export default function InterruptBar({ onInterrupt, disabled }) {
  const [message, setMessage] = useState('')
  const [sending, setSending] = useState(false)
  const [notice, setNotice] = useState(null)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!message.trim() || disabled || sending) return

    setSending(true)
    setNotice(null)
    try {
      const ok = await onInterrupt(message.trim())
      if (ok) {
        setMessage('')
        setNotice('Queued. The next speaker will address you directly.')
      } else {
        setNotice('Interrupt failed. The debate may already be closed.')
      }
    } finally {
      setSending(false)
    }
  }

  return (
    <section className="arena-panel interrupt-panel">
      <div className="flex items-center gap-2 mb-3">
        <AgentIcon agent="human" size={14} className="agent-human" />
        <div className="eyebrow mb-0">Jump In Mid-Debate</div>
      </div>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3 md:flex-row">
        <input
          type="text"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          maxLength={280}
          disabled={disabled || sending}
          placeholder="Challenge a claim, ask a question, or push one side harder..."
          className="arena-input flex-1 px-4 py-3"
        />
        <button
          type="submit"
          disabled={!message.trim() || disabled || sending}
          className="arena-btn hero-cta px-5 py-3 md:min-w-[148px]"
        >
          {sending ? 'Sending...' : 'Jump In'}
        </button>
      </form>

      <div className="mt-3 flex flex-col gap-2 text-xs font-mono uppercase tracking-[0.18em] sm:flex-row sm:items-center sm:justify-between">
        <span className="text-slate-500">{280 - message.length} characters left</span>
        <span className={notice ? 'break-words text-arena-human sm:text-right' : 'break-words text-slate-500 sm:text-right'}>
          {notice || 'Interrupts are routed into the live queue'}
        </span>
      </div>
    </section>
  )
}
