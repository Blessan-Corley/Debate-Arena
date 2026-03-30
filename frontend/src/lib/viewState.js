export function shouldShowHomeScreen({
  status,
  feedCount = 0,
  debateId = null,
  selectedHistory = false,
}) {
  if (selectedHistory) return false
  if (status === 'idle') return true
  if (status === 'error' && !debateId && feedCount === 0) return true
  return false
}
