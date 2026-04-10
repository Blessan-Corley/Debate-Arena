import { describe, expect, it } from 'vitest'

import { getHistoryColumnClass } from './layout'

describe('getHistoryColumnClass', () => {
  it('keeps the archive stacked until extra-wide screens when collapsed', () => {
    expect(getHistoryColumnClass(true)).toBe('xl:grid-cols-[minmax(0,1fr)_176px]')
  })

  it('keeps the expanded archive stacked until extra-wide screens', () => {
    expect(getHistoryColumnClass(false)).toBe('xl:grid-cols-[minmax(0,1fr)_360px]')
  })
})
