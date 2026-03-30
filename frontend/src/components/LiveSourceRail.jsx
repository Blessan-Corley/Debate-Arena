import { getProviderLabel } from '../lib/arenaPresentation'
import { buildSourceFeedState } from '../lib/sourceFeed'


function SourceFeedList({ sources, interactive }) {
  return (
    <div className="source-feed-list">
      {sources.map((source, index) => {
        const key = `${source.provider}-${source.url}-${index}`
        const content = (
          <>
            <div className="source-card-topline">
              <span className="source-provider">{getProviderLabel(source.provider)}</span>
              <span className="source-link">{source.host}</span>
            </div>
            <div className="source-card-title">
              {source.title}
            </div>
            <div className="source-card-snippet">
              {source.snippet}
            </div>
            <div className="source-card-footer">
              {interactive ? 'Open source' : 'Live evidence'}
            </div>
          </>
        )

        if (!interactive) {
          return (
            <div key={key} className="source-card">
              {content}
            </div>
          )
        }

        return (
          <a
            key={key}
            href={source.url}
            target="_blank"
            rel="noreferrer"
            className="source-card"
          >
            {content}
          </a>
        )
      })}
    </div>
  )
}


export default function LiveSourceRail({
  sources,
  mode = 'compact',
  onOpen,
  onClose,
}) {
  const { all, preview, hiddenCount } = buildSourceFeedState(sources, 2)

  if (mode === 'modal') {
    return (
      <div className="source-modal-backdrop" onClick={onClose}>
        <div
          className="source-modal-panel"
          role="dialog"
          aria-modal="true"
          aria-label="Live source feed"
          onClick={(event) => event.stopPropagation()}
        >
          <div className="source-modal-header">
            <div>
              <div className="eyebrow">Live Data</div>
              <div className="source-rail-title-row">
                <h3 className="panel-title">Source Feed</h3>
                <span className="source-count-badge">{all.length}</span>
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="arena-btn subtle-btn source-modal-close"
            >
              Close
            </button>
          </div>

          {all.length === 0 ? (
            <p className="text-sm text-slate-400">
              Search activity and cited web sources will appear here as the agents fetch live data.
            </p>
          ) : (
            <div className="source-modal-scroll">
              <SourceFeedList sources={all} interactive />
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={onOpen}
      className="arena-panel arena-rail-panel source-rail-compact"
    >
      <div className="source-rail-header">
        <div className="eyebrow">Live Data</div>
        <div className="source-rail-title-row">
          <h3 className="panel-title">Source Feed</h3>
          <span className="source-count-badge">{all.length}</span>
        </div>
      </div>

      {all.length === 0 ? (
        <p className="text-sm text-slate-400">
          Search activity and cited web sources will appear here as the agents fetch live data.
        </p>
      ) : (
        <>
          <SourceFeedList sources={preview} interactive={false} />
          <div className="source-compact-footer">
            <span>{hiddenCount > 0 ? `+${hiddenCount} more sources` : 'Open full feed'}</span>
            <span className="source-open-arrow" aria-hidden="true">View</span>
          </div>
        </>
      )}
    </button>
  )
}
