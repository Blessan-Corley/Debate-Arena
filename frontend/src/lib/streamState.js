export function shouldFlagUnexpectedStreamEnd({
  receivedEnd,
  sawSystemError,
  aborted,
}) {
  if (aborted) return false
  if (receivedEnd) return false
  if (sawSystemError) return false
  return true
}
