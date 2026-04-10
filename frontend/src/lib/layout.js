export function getHistoryColumnClass(collapsed) {
  return collapsed
    ? 'xl:grid-cols-[minmax(0,1fr)_176px]'
    : 'xl:grid-cols-[minmax(0,1fr)_360px]'
}
