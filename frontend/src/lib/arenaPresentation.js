const AGENT_PRESENTATION = {
  host: {
    name: 'GOPINATH',
    shortName: 'Gopinath',
    role: 'Host',
    thinking: 'Gopinath is setting the stage...',
  },
  pro: {
    name: 'BLESSAN',
    shortName: 'Blessan',
    role: 'Pro',
    thinking: 'Blessan is aligning evidence...',
  },
  con: {
    name: 'PRANAV',
    shortName: 'Pranav',
    role: 'Con',
    thinking: 'Pranav is checking the pressure points...',
  },
  crowd: {
    name: 'THE CROWD',
    shortName: 'Crowd',
    role: 'Crowd',
    thinking: 'The crowd is deciding if that actually landed...',
  },
  judge: {
    name: 'PRADHAKSHINI',
    shortName: 'Pradhakshini',
    role: 'Judge',
    thinking: 'Pradhakshini is weighing the record...',
  },
  human: {
    name: 'YOU',
    shortName: 'You',
    role: 'Audience',
    thinking: 'You are stepping into the arena...',
  },
  system: {
    name: 'SYSTEM',
    shortName: 'System',
    role: 'Arena',
    thinking: 'The arena is syncing...',
  },
}

export function getAgentPresentation(agent) {
  return AGENT_PRESENTATION[agent] || AGENT_PRESENTATION.host
}

export function getProviderLabel(provider) {
  return provider === 'tavily' ? 'Tavily' : 'Google Search'
}

function truncate(value, maxLength) {
  if (!value) return ''
  return value.length <= maxLength ? value : `${value.slice(0, maxLength - 3).trimEnd()}...`
}

function extractHost(url) {
  if (!url) return 'Source unavailable'
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return 'Source unavailable'
  }
}

export function normalizeSource(source = {}) {
  return {
    title: truncate(source.title || 'Untitled source', 110),
    snippet: truncate(source.snippet || 'No summary available for this live fetch.', 220),
    url: source.url || '',
    host: extractHost(source.url || ''),
    provider: source.provider || 'google-search',
    providerLabel: getProviderLabel(source.provider || 'google-search'),
  }
}

export function getWinnerLabel(winner) {
  if (winner === 'pro') return AGENT_PRESENTATION.pro.shortName
  if (winner === 'con') return AGENT_PRESENTATION.con.shortName
  if (winner === 'tie') return 'Tie'
  return winner || 'Pending'
}
