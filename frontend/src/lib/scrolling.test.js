import { describe, expect, it } from 'vitest'

import { isNearBottom } from './scrolling'

describe('isNearBottom', () => {
  it('returns true when the viewport is close to the bottom', () => {
    expect(isNearBottom({ scrollTop: 540, clientHeight: 400, scrollHeight: 980 }, 48)).toBe(true)
  })

  it('returns false when the viewport is far from the bottom', () => {
    expect(isNearBottom({ scrollTop: 420, clientHeight: 400, scrollHeight: 980 }, 48)).toBe(false)
  })
})
