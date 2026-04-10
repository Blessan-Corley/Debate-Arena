import { useState } from 'react'

import AgentIcon from './AgentIcon'
import { getAgentPresentation } from '../lib/arenaPresentation'


const EXAMPLE_TOPICS = [
  'AI should replace middle management in large companies',
  'Universal basic income is a better answer than job retraining',
  'Open-source AI is safer for society than closed AI',
  'Nuclear power is the fastest realistic path to clean energy',
]


export default function TopicInput({ onStart, disabled }) {
  const [topic, setTopic] = useState('')
  const [rounds, setRounds] = useState(4)
  const pro = getAgentPresentation('pro')
  const con = getAgentPresentation('con')
  const crowd = getAgentPresentation('crowd')
  const judge = getAgentPresentation('judge')

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!topic.trim() || disabled) return
    onStart(topic.trim(), rounds)
  }

  return (
    <section className="arena-panel hero-panel">
      <div className="eyebrow">Multi-Agent AI Debate Arena</div>
      <h1 className="hero-title">THE ARENA</h1>
      <p className="hero-copy">
        Five AI roles. Live search. Human interruptions. One judge that decides when the clash is finally over.
      </p>

      <div className="flex flex-wrap gap-3 mt-5 text-xs font-mono uppercase tracking-[0.18em] text-slate-400">
        <span className="inline-flex items-center gap-2"><AgentIcon agent="pro" size={13} className="agent-pro" /> {pro.shortName}</span>
        <span className="inline-flex items-center gap-2"><AgentIcon agent="con" size={13} className="agent-con" /> {con.shortName}</span>
        <span className="inline-flex items-center gap-2"><AgentIcon agent="crowd" size={13} className="agent-crowd" /> {crowd.shortName}</span>
        <span className="inline-flex items-center gap-2"><AgentIcon agent="judge" size={13} className="agent-judge" /> {judge.shortName}</span>
      </div>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5">
        <div>
          <label className="eyebrow mb-2 block">Tonight&apos;s Motion</label>
          <textarea
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Enter a debate motion, controversial statement, or policy question..."
            rows={3}
            className="arena-input hero-input w-full px-4 py-4 resize-none"
            disabled={disabled}
          />
        </div>

        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="min-w-0">
            <label className="eyebrow mb-2 block">Debate Length</label>
            <div className="flex flex-wrap gap-2">
              {[4, 5, 6].map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setRounds(value)}
                  className={`depth-chip ${rounds === value ? 'depth-chip-active' : ''}`}
                >
                  {value}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={!topic.trim() || disabled}
            className="arena-btn hero-cta w-full px-6 py-4 md:w-auto"
          >
            Enter The Arena
          </button>
        </div>
      </form>

      <div className="mt-8">
        <div className="eyebrow mb-3">Quick Starts</div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_TOPICS.map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => setTopic(example)}
              className="quick-topic"
            >
              {example}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
