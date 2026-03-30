import { describe, expect, it } from 'vitest'

import { getHistoryColumnClass } from './layout'

describe('getHistoryColumnClass', () => {
  it('uses a wider collapsed archive rail so controls stay visible', () => {
    expect(getHistoryColumnClass(true)).toBe('lg:grid-cols-[minmax(0,1fr)_156px]')
  })

  it('keeps the expanded archive rail width unchanged', () => {
    expect(getHistoryColumnClass(false)).toBe('lg:grid-cols-[minmax(0,1fr)_340px]')
  })
})
