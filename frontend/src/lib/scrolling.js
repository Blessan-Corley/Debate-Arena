export function isNearBottom(nodeLike, threshold = 96) {
  if (!nodeLike) return true
  const distance = nodeLike.scrollHeight - (nodeLike.scrollTop + nodeLike.clientHeight)
  return distance <= threshold
}
