import { useCallback, useEffect, useRef, useState } from 'react'

import { apiJson, apiUrl } from '../lib/api'
import { applyDebateEvent, createInitialDebateState } from '../lib/debateState'
import { shouldFlagUnexpectedStreamEnd } from '../lib/streamState'


export function useDebateStream() {
  const [arena, setArena] = useState(createInitialDebateState())
  const [historyItems, setHistoryItems] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [deletingHistoryId, setDeletingHistoryId] = useState(null)
  const [selectedHistory, setSelectedHistory] = useState(null)
  const [selectedHistoryLoading, setSelectedHistoryLoading] = useState(false)
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)
  const abortRef = useRef(null)

  const loadHistory = useCallback(async () => {
    setHistoryLoading(true)
    try {
      const data = await apiJson('/debate/history?limit=30')
      setHistoryItems(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setHistoryLoading(false)
    }
  }, [])

  useEffect(() => {
    loadHistory()
  }, [loadHistory])

  const openHistory = useCallback(async (debateId) => {
    setSelectedHistoryLoading(true)
    setError(null)
    try {
      const data = await apiJson(`/debate/history/${debateId}`)
      setSelectedHistory(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setSelectedHistoryLoading(false)
    }
  }, [])

  const closeHistory = useCallback(() => {
    setSelectedHistory(null)
  }, [])

  const deleteHistory = useCallback(async (debateId) => {
    setDeletingHistoryId(debateId)
    setError(null)
    try {
      await apiJson(`/debate/history/${debateId}`, {
        method: 'DELETE',
      })

      setHistoryItems(prev => prev.filter(item => item.debate_id !== debateId))
      setSelectedHistory(prev => prev?.debate_id === debateId ? null : prev)

      setArena(prev => (
        prev.debateId === debateId
          ? createInitialDebateState()
          : prev
      ))
      setStatus(prev => (arena.debateId === debateId && prev !== 'running' ? 'idle' : prev))
      return true
    } catch (err) {
      setError(err.message)
      return false
    } finally {
      setDeletingHistoryId(null)
    }
  }, [arena.debateId])

  const pushEvent = useCallback((event) => {
    setArena(prev => applyDebateEvent(prev, event))
  }, [])

  const startDebate = useCallback(async (topic, rounds = 4) => {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setArena(createInitialDebateState())
    setSelectedHistory(null)
    setStatus('connecting')
    setError(null)

    let receivedEnd = false
    let sawSystemError = false

    try {
      const response = await fetch(apiUrl('/debate/start'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, rounds }),
        signal: controller.signal,
      })

      if (!response.ok) {
        const contentType = response.headers.get('content-type') || ''
        const detail = contentType.includes('application/json')
          ? await response.json()
          : await response.text()
        const message = typeof detail === 'object' && detail
          ? detail.detail || detail.message
          : detail
        throw new Error(message || 'Failed to start debate')
      }

      if (!response.body) {
        throw new Error('The debate stream could not be opened.')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let currentEventType = null

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const segments = buffer.split('\n')
        buffer = segments.pop() || ''

        for (const line of segments) {
          if (!line.trim()) continue
          if (line.startsWith('event: ')) {
            currentEventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const rawData = line.slice(6).trim()
            if (!rawData) continue
            try {
              const event = JSON.parse(rawData)
              pushEvent({
                ...event,
                type: currentEventType || event.type,
              })
              if ((currentEventType || event.type) === 'debate_start') {
                setStatus('running')
              }
              if ((currentEventType || event.type) === 'debate_end') {
                receivedEnd = true
                setStatus('ended')
              }
              if ((currentEventType || event.type) === 'system_error') {
                sawSystemError = true
                setStatus('error')
                setError(event.metadata?.error || event.message)
              }
            } catch {
              // Ignore malformed SSE payloads.
            }
          }
        }
      }

      if (shouldFlagUnexpectedStreamEnd({
        receivedEnd,
        sawSystemError,
        aborted: controller.signal.aborted,
      })) {
        setStatus('error')
        setError('The live debate stream ended unexpectedly.')
      } else if (receivedEnd) {
        await loadHistory()
      }
    } catch (err) {
      if (err.name === 'AbortError') return
      setStatus('error')
      setError(err.message)
    }
  }, [loadHistory, pushEvent])

  const sendInterrupt = useCallback(async (message) => {
    if (!arena.debateId || status !== 'running') return false
    try {
      await apiJson('/debate/interrupt', {
        method: 'POST',
        body: JSON.stringify({
          debate_id: arena.debateId,
          message,
        }),
      })
      return true
    } catch {
      return false
    }
  }, [arena.debateId, status])

  const submitFeedback = useCallback(async (rating, comment, winnerPick) => {
    if (!arena.debateId) return false
    try {
      await apiJson('/debate/feedback', {
        method: 'POST',
        body: JSON.stringify({
          debate_id: arena.debateId,
          rating,
          comment: comment || null,
          winner_pick: winnerPick || null,
        }),
      })
      await loadHistory()
      return true
    } catch {
      return false
    }
  }, [arena.debateId, loadHistory])

  const reset = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    setArena(createInitialDebateState())
    setStatus('idle')
    setError(null)
  }, [])

  return {
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
  }
}
