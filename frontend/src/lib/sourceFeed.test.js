import { describe, expect, it } from 'vitest'

import { buildSourceFeedState } from './sourceFeed'

describe('buildSourceFeedState', () => {
  it('dedupes sources and keeps a compact preview plus hidden count', () => {
    const state = buildSourceFeedState([
      { title: 'One', url: 'https://a.example/article', snippet: 'A', provider: 'tavily' },
      { title: 'Two', url: 'https://b.example/article', snippet: 'B', provider: 'google-search' },
      { title: 'One duplicate', url: 'https://a.example/article', snippet: 'A2', provider: 'tavily' },
    ], 1)

    expect(state.all).toHaveLength(2)
    expect(state.preview).toHaveLength(1)
    expect(state.preview[0].title).toBe('One duplicate')
    expect(state.hiddenCount).toBe(1)
  })
})
