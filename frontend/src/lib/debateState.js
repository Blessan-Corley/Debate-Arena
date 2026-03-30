export function createInitialDebateState() {
  return {
    debateId: null,
    status: 'idle',
    error: null,
    feed: [],
    liveSources: [],
    thinkingAgent: null,
    winner: null,
  }
}

function createFeedItem(event) {
  return {
    id: event.id || `${event.agent}-${event.type}-${event.created_at}-${Math.random().toString(36).slice(2, 8)}`,
    agent: event.agent,
    type: event.type,
    message: event.message,
    metadata: event.metadata || {},
    createdAt: event.created_at,
  }
}

export function hydrateStoredMessages(messages = []) {
  return messages.map(message => createFeedItem({
    ...message,
    id: message.id,
    created_at: message.created_at,
  }))
}

export function applyDebateEvent(state, event) {
  const next = {
    ...state,
    debateId: event.debate_id || state.debateId,
  }

  switch (event.type) {
    case 'debate_start':
      return {
        ...next,
        status: 'running',
      }

    case 'thinking':
      return {
        ...next,
        thinkingAgent: event.agent,
      }

    case 'debate_end':
      return {
        ...next,
        status: 'ended',
        thinkingAgent: null,
        winner: event.metadata?.winner || state.winner,
      }

    case 'system_error':
      return {
        ...next,
        status: 'error',
        thinkingAgent: null,
        error: event.metadata?.error || event.message,
        feed: [...state.feed, createFeedItem(event)],
      }

    default: {
      const liveSources = event.type === 'search_complete'
        ? [...state.liveSources, ...(event.metadata?.sources || [])]
        : state.liveSources

      return {
        ...next,
        feed: [...state.feed, createFeedItem(event)],
        liveSources,
        thinkingAgent: null,
        winner: event.metadata?.winner || state.winner,
      }
    }
  }
}
