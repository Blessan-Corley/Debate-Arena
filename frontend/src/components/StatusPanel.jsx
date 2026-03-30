import { getWinnerLabel } from '../lib/arenaPresentation'


export default function StatusPanel({ status, winner, debateId, feedCount, sourceCount }) {
  const title = status === 'running'
    ? 'Ongoing'
    : status === 'ended'
      ? 'Verdict Reached'
      : status === 'connecting'
        ? 'Connecting'
        : status === 'error'
          ? 'Interrupted'
          : 'Standby'

  return (
    <section className="arena-panel status-panel">
      <div className="eyebrow">Debate Status</div>
      <div className="panel-title mb-4">{title}</div>

      <div className="status-metric">
        <span>Winner</span>
        <strong>{getWinnerLabel(winner)}</strong>
      </div>
      <div className="status-metric">
        <span>Feed Events</span>
        <strong>{feedCount}</strong>
      </div>
      <div className="status-metric">
        <span>Live Sources</span>
        <strong>{sourceCount}</strong>
      </div>
      <div className="status-metric">
        <span>Debate ID</span>
        <strong className="truncate">{debateId || 'Not started'}</strong>
      </div>
    </section>
  )
}
