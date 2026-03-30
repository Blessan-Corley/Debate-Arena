import { describe, expect, test } from 'vitest'

import { shouldShowHomeScreen } from './viewState'


describe('shouldShowHomeScreen', () => {
  test('shows home screen while idle with no active debate', () => {
    expect(shouldShowHomeScreen({
      status: 'idle',
      feedCount: 0,
      debateId: null,
      selectedHistory: false,
    })).toBe(true)
  })

  test('keeps arena mounted when a live debate errors after messages exist', () => {
    expect(shouldShowHomeScreen({
      status: 'error',
      feedCount: 3,
      debateId: 'debate-123',
      selectedHistory: false,
    })).toBe(false)
  })
})
