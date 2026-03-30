import { describe, expect, it } from 'vitest'

import { applyDebateEvent, createInitialDebateState } from './debateState'

describe('debate state reducer', () => {
  it('adds search sources and visible feed items from search events', () => {
    const state = createInitialDebateState()

    const next = applyDebateEvent(state, {
      type: 'search_complete',
      agent: 'pro',
      message: 'Victor found three live sources.',
      debate_id: 'debate-123',
      created_at: '2026-03-30T12:00:00Z',
      metadata: {
        provider: 'tavily',
        sources: [
          { title: 'Source A', url: 'https://example.com/a', snippet: 'A', provider: 'tavily' },
          { title: 'Source B', url: 'https://example.com/b', snippet: 'B', provider: 'tavily' },
        ],
      },
    })

    expect(next.feed).toHaveLength(1)
    expect(next.feed[0].type).toBe('search_complete')
    expect(next.liveSources).toHaveLength(2)
    expect(next.debateId).toBe('debate-123')
  })

  it('moves to ended state when the debate_end event arrives', () => {
    const state = {
      ...createInitialDebateState(),
      status: 'running',
      debateId: 'debate-123',
    }

    const next = applyDebateEvent(state, {
      type: 'debate_end',
      agent: 'system',
      message: 'Debate ended.',
      debate_id: 'debate-123',
      created_at: '2026-03-30T12:10:00Z',
      metadata: { winner: 'con' },
    })

    expect(next.status).toBe('ended')
    expect(next.winner).toBe('con')
  })
})
