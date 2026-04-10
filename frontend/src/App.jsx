import { useCallback, useMemo, useState } from 'react'

import DebateArena from './components/DebateArena'
import FeedbackPanel from './components/FeedbackPanel'
import HistoryPanel from './components/HistoryPanel'
import TopicInput from './components/TopicInput'
import { useDebateStream } from './hooks/useDebateStream'
import { hydrateStoredMessages } from './lib/debateState'
import { getHistoryColumnClass } from './lib/layout'
import { shouldShowHomeScreen } from './lib/viewState'


export default function App() {
  const [currentTopic, setCurrentTopic] = useState('')
  const [historyCollapsed, setHistoryCollapsed] = useState(false)
  const {
    arena,
    historyItems,
    historyLoading,
    deletingHistoryId,
    selectedHistory,
    selectedHistoryLoading,
    status,
    error,
    startDebate,
    sendInterrupt,
    submitFeedback,
    loadHistory,
    openHistory,
    closeHistory,
    deleteHistory,
    reset,
  } = useDebateStream()

  const handleStart = useCallback((topic, rounds) => {
    setCurrentTopic(topic)
    startDebate(topic, rounds)
  }, [startDebate])

  const handleReset = useCallback(() => {
    setCurrentTopic('')
    closeHistory()
    reset()
  }, [closeHistory, reset])

  const archiveFeed = useMemo(
    () => hydrateStoredMessages(selectedHistory?.messages || []),
    [selectedHistory],
  )

  const historyColumnClass = getHistoryColumnClass(historyCollapsed)
  const showHomeScreen = shouldShowHomeScreen({
    status,
    feedCount: arena.feed.length,
    debateId: arena.debateId,
    selectedHistory: Boolean(selectedHistory),
  })

  if (selectedHistory) {
    return (
      <div className="min-h-screen px-3 py-4 sm:px-4 sm:py-6 lg:px-6">
        <div className={`mx-auto grid w-full max-w-[1600px] min-w-0 items-start gap-4 sm:gap-6 ${historyColumnClass}`}>
          <DebateArena
            topic={selectedHistory.topic}
            feed={archiveFeed}
            liveSources={[]}
            thinkingAgent={null}
            status={selectedHistory.status}
            debateId={selectedHistory.debate_id}
            winner={selectedHistory.winner}
            onInterrupt={() => false}
            onReset={handleReset}
            readOnly
          />
          <HistoryPanel
            items={historyItems}
            loading={historyLoading || selectedHistoryLoading}
            onOpen={openHistory}
            onRefresh={loadHistory}
            onDelete={deleteHistory}
            selectedId={selectedHistory.debate_id}
            deletingId={deletingHistoryId}
            collapsed={historyCollapsed}
            onToggle={() => setHistoryCollapsed(value => !value)}
            compact
          />
        </div>
      </div>
    )
  }

  if (showHomeScreen) {
    return (
      <div className="min-h-screen px-3 py-4 sm:px-4 sm:py-8 lg:px-6">
        <div className={`mx-auto grid w-full max-w-[1600px] min-w-0 items-start gap-4 sm:gap-6 ${historyColumnClass}`}>
          <div className="min-w-0 space-y-5">
            <TopicInput onStart={handleStart} disabled={false} />
            {error && (
              <div className="arena-panel border border-red-400/30 text-red-200">
                {error}
              </div>
            )}
          </div>
          <HistoryPanel
            items={historyItems}
            loading={historyLoading}
            onOpen={openHistory}
            onRefresh={loadHistory}
            onDelete={deleteHistory}
            selectedId={null}
            deletingId={deletingHistoryId}
            collapsed={historyCollapsed}
            onToggle={() => setHistoryCollapsed(value => !value)}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen px-3 py-4 sm:px-4 sm:py-6 lg:px-6">
      <DebateArena
        topic={currentTopic}
        feed={arena.feed}
        liveSources={arena.liveSources}
        thinkingAgent={arena.thinkingAgent}
        status={status}
        debateId={arena.debateId}
        winner={arena.winner}
        onInterrupt={sendInterrupt}
        onReset={handleReset}
        feedbackSlot={
          status === 'ended' ? (
            <FeedbackPanel onSubmit={submitFeedback} onReset={handleReset} />
          ) : status === 'error' ? (
            <section className="arena-panel border border-red-400/30 text-red-200">
              {error || 'The live debate encountered an error.'}
            </section>
          ) : null
        }
      />
    </div>
  )
}
