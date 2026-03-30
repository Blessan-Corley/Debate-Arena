export function getHistoryColumnClass(collapsed) {
  return collapsed
    ? 'lg:grid-cols-[minmax(0,1fr)_156px]'
    : 'lg:grid-cols-[minmax(0,1fr)_340px]'
}
