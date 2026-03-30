import { describe, expect, it } from 'vitest'

import { networkErrorMessage } from './api'

describe('networkErrorMessage', () => {
  it('points the user to the backend URL when a request cannot be reached', () => {
    expect(networkErrorMessage('/debate/history')).toContain('Cannot reach the backend')
    expect(networkErrorMessage('/debate/history')).toContain('/debate/history')
  })
})
