import AgentIcon from './AgentIcon'


function ArchiveControls({ collapsed, onRefresh, onToggle }) {
  return (
    <div className="history-control-row">
      <button
        type="button"
        aria-label="Refresh archive"
        onClick={onRefresh}
        className="arena-btn subtle-btn history-icon-btn"
      >
        <svg viewBox="0 0 24 24" className="history-icon" aria-hidden="true">
          <path
            d="M20 11a8 8 0 1 0 2 5.3"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
          <path
            d="M20 4v7h-7"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>
      <button
        type="button"
        aria-label={collapsed ? 'Expand archive' : 'Collapse archive'}
        aria-pressed={collapsed}
        onClick={onToggle}
        className="arena-btn subtle-btn history-icon-btn"
      >
        <span className="history-hamburger" aria-hidden="true">
          <span />
          <span />
          <span />
        </span>
      </button>
    </div>
  )
}


function HistoryCard({ item, selectedId, onOpen, onDelete, deletingId }) {
  return (
    <div className={`history-card text-left w-full ${selectedId === item.debate_id ? 'history-card-active' : ''}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="font-mono text-[11px] uppercase tracking-[0.26em] text-slate-500">
            {item.status}
          </div>
          <div className="font-body text-base text-slate-100 mt-1 max-h-14 overflow-hidden">
            {item.topic}
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <AgentIcon
            agent={item.winner === 'con' ? 'con' : item.winner === 'pro' ? 'pro' : 'judge'}
            size={14}
            className={item.winner === 'con' ? 'agent-con' : item.winner === 'pro' ? 'agent-pro' : 'agent-judge'}
          />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3 text-[11px] font-mono uppercase tracking-[0.18em] text-slate-500">
        <span>{item.message_count} events</span>
        <span>{item.winner || 'no winner yet'}</span>
      </div>
      <div className="mt-4 flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={() => onOpen(item.debate_id)}
          className="arena-btn subtle-btn px-3 py-2"
        >
          Open
        </button>
        <button
          type="button"
          onClick={() => onDelete(item.debate_id)}
          disabled={deletingId === item.debate_id}
          className="arena-btn history-delete-btn"
        >
          {deletingId === item.debate_id ? 'Deleting' : 'Delete'}
        </button>
      </div>
    </div>
  )
}


export default function HistoryPanel({
  items,
  loading,
  onOpen,
  onRefresh,
  onDelete,
  selectedId,
  deletingId = null,
  collapsed = false,
  onToggle,
  compact = false,
}) {
  if (collapsed) {
    return (
      <section className="arena-panel history-panel-collapsed">
        <div className="history-panel-header history-panel-header-collapsed">
          <div className="eyebrow">Archive</div>
          <ArchiveControls collapsed={collapsed} onRefresh={onRefresh} onToggle={onToggle} />
        </div>
        <div className="panel-title mt-2">{items.length}</div>
        <div className="text-xs text-slate-500 uppercase tracking-[0.18em]">Saved debates</div>
      </section>
    )
  }

  return (
    <section className="arena-panel h-full history-panel-shell">
      <div className="history-panel-header mb-4">
        <div>
          <div className="eyebrow">Previous Debates</div>
          <h3 className="panel-title">Arena Archive</h3>
        </div>
        <ArchiveControls collapsed={collapsed} onRefresh={onRefresh} onToggle={onToggle} />
      </div>

      {loading ? (
        <div className="text-sm text-slate-400">Loading previous debates...</div>
      ) : items.length === 0 ? (
        <div className="text-sm text-slate-400">No debates stored yet.</div>
      ) : (
        <div className={`history-scroll ${compact ? 'history-scroll-compact' : ''}`}>
          {items.map((item) => (
            <HistoryCard
              key={item.debate_id}
              item={item}
              selectedId={selectedId}
              onOpen={onOpen}
              onDelete={onDelete}
              deletingId={deletingId}
            />
          ))}
        </div>
      )}
    </section>
  )
}
