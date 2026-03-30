import { describe, expect, it } from 'vitest'

import {
  getAgentPresentation,
  getWinnerLabel,
  normalizeSource,
} from './arenaPresentation'

describe('arenaPresentation', () => {
  it('returns the requested custom agent names', () => {
    expect(getAgentPresentation('host').name).toBe('GOPINATH')
    expect(getAgentPresentation('pro').name).toBe('BLESSAN')
    expect(getAgentPresentation('con').name).toBe('PRANAV')
    expect(getAgentPresentation('judge').name).toBe('PRADHAKSHINI')
  })

  it('normalizes live source cards with readable fallbacks', () => {
    expect(normalizeSource({ provider: 'tavily' })).toEqual({
      title: 'Untitled source',
      snippet: 'No summary available for this live fetch.',
      url: '',
      host: 'Source unavailable',
      provider: 'tavily',
      providerLabel: 'Tavily',
    })
  })

  it('maps winner labels to the renamed debaters', () => {
    expect(getWinnerLabel('pro')).toBe('Blessan')
    expect(getWinnerLabel('con')).toBe('Pranav')
    expect(getWinnerLabel('tie')).toBe('Tie')
  })
})
