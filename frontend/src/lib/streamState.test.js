import { describe, expect, test } from 'vitest'

import { shouldFlagUnexpectedStreamEnd } from './streamState'


describe('shouldFlagUnexpectedStreamEnd', () => {
  test('flags a dropped stream with no terminal event', () => {
    expect(shouldFlagUnexpectedStreamEnd({
      receivedEnd: false,
      sawSystemError: false,
      aborted: false,
    })).toBe(true)
  })

  test('does not flag unexpected end after a system error event already arrived', () => {
    expect(shouldFlagUnexpectedStreamEnd({
      receivedEnd: false,
      sawSystemError: true,
      aborted: false,
    })).toBe(false)
  })
})
