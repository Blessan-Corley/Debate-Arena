import { normalizeSource } from './arenaPresentation'


export function buildSourceFeedState(sources = [], previewLimit = 2) {
  const seen = new Set()
  const all = []

  for (const source of [...sources].reverse()) {
    const normalized = normalizeSource(source)
    const key = `${normalized.provider}:${normalized.url || normalized.title}`
    if (seen.has(key)) continue
    seen.add(key)
    all.push(normalized)
  }

  const preview = all.slice(0, previewLimit)

  return {
    all,
    preview,
    hiddenCount: Math.max(0, all.length - preview.length),
  }
}
