import { useEffect, useMemo, useRef, useState } from 'react'

import { isNearBottom } from '../lib/scrolling'
import AgentMessage from './AgentMessage'
import InterruptBar from './InterruptBar'
import LiveSourceRail from './LiveSourceRail'
import StatusPanel from './StatusPanel'
import ThinkingIndicator from './ThinkingIndicator'


function collectSources(feed, liveSources) {
  const fromFeed = feed.flatMap(item => item.metadata?.sources || [])
  return [...liveSources, ...fromFeed]
}


export default function DebateArena({
  topic,
  feed,
  liveSources,
  thinkingAgent,
  status,
  debateId,
  winner,
  onInterrupt,
  onReset,
  readOnly = false,
  feedbackSlot = null,
}) {
  const feedScrollRef = useRef(null)
  const shouldStickRef = useRef(true)
  const [sourceFeedOpen, setSourceFeedOpen] = useState(false)

  useEffect(() => {
    const node = feedScrollRef.current
    if (!node || !shouldStickRef.current) return
    node.scrollTop = node.scrollHeight
  }, [feed.length, thinkingAgent, Boolean(feedbackSlot)])

  const sources = useMemo(() => collectSources(feed, liveSources), [feed, liveSources])

  useEffect(() => {
    if (!sourceFeedOpen) return undefined

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setSourceFeedOpen(false)
      }
    }

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [sourceFeedOpen])

  const handleFeedScroll = () => {
    const node = feedScrollRef.current
    if (!node) return
    shouldStickRef.current = isNearBottom(node, 112)
  }

  return (
    <div className="arena-shell mx-auto w-full max-w-7xl min-w-0">
      <header className="arena-header">
        <div className="min-w-0 flex-1">
          <div className="eyebrow">Live Debate Feed</div>
          <h1 className="arena-topic">
            {topic ? `"${topic}"` : 'Debate Archive'}
          </h1>
        </div>
        <button
          type="button"
          onClick={onReset}
          className="arena-btn subtle-btn w-full px-4 py-2 sm:w-auto"
        >
          {readOnly ? 'Back' : 'Reset'}
        </button>
      </header>

      <div className="arena-stage">
        <section className="arena-panel arena-feed-panel min-w-0">
          <div
            ref={feedScrollRef}
            onScroll={handleFeedScroll}
            className="arena-feed-scroll"
          >
            <div className="space-y-4">
              {feed.map(item => (
                <AgentMessage key={item.id} item={item} />
              ))}
              {thinkingAgent && !readOnly && <ThinkingIndicator agent={thinkingAgent} />}
              {feedbackSlot}
            </div>
          </div>
        </section>

        <aside className="arena-side-column min-w-0">
          <StatusPanel
            status={status}
            winner={winner}
            debateId={debateId}
            feedCount={feed.length}
            sourceCount={sources.length}
          />
          <LiveSourceRail
            sources={sources}
            onOpen={() => setSourceFeedOpen(true)}
          />
        </aside>
      </div>

      {!readOnly && (
        <div className="arena-control-dock">
          <InterruptBar onInterrupt={onInterrupt} disabled={status !== 'running'} />
        </div>
      )}

      {sourceFeedOpen && (
        <LiveSourceRail
          mode="modal"
          sources={sources}
          onClose={() => setSourceFeedOpen(false)}
        />
      )}
    </div>
  )
}
