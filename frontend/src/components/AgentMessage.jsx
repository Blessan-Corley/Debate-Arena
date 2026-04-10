import AgentIcon from './AgentIcon'
import { getAgentPresentation, getProviderLabel, normalizeSource } from '../lib/arenaPresentation'


const AGENT_CONFIG = {
  host: { colorClass: 'agent-host', borderClass: 'border-host', align: 'center' },
  pro: { colorClass: 'agent-pro', borderClass: 'border-pro', align: 'left' },
  con: { colorClass: 'agent-con', borderClass: 'border-con', align: 'right' },
  crowd: { colorClass: 'agent-crowd', borderClass: 'border-crowd', align: 'center' },
  judge: { colorClass: 'agent-judge', borderClass: 'border-judge', align: 'center' },
  human: { colorClass: 'agent-human', borderClass: 'border-human', align: 'left' },
  system: { colorClass: 'text-red-300', borderClass: 'border-red-400/40', align: 'center' },
}


function alignmentClass(align) {
  if (align === 'left') return 'mr-auto'
  if (align === 'right') return 'ml-auto'
  return 'mx-auto'
}


function SearchCard({ item, config }) {
  const sources = item.metadata?.sources || []
  const presentation = getAgentPresentation(item.agent)

  return (
    <div className={`feed-card ${alignmentClass(config.align)} max-w-3xl min-w-0 w-full border ${config.borderClass}`}>
      <div className="feed-meta">
        <AgentIcon agent={item.agent} size={14} className={config.colorClass} />
        <span className={config.colorClass}>{presentation.name}</span>
        <span className="text-slate-500">
          {item.type === 'search_started' ? 'Live Search Started' : 'Live Search Complete'}
        </span>
      </div>
      <p className="mt-3 break-words text-slate-200 leading-relaxed">{item.message}</p>
      {item.metadata?.query && (
        <div className="mt-3 break-all text-xs font-mono uppercase tracking-[0.18em] text-slate-500">
          Query: {item.metadata.query}
        </div>
      )}
      {sources.length > 0 && (
        <div className="mt-4 grid gap-2">
          {sources.slice(0, 3).map((source, index) => {
            const normalized = normalizeSource(source)
            return (
            <a
              key={`${normalized.url}-${index}`}
              href={normalized.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex min-w-0 flex-wrap items-center gap-2 text-sm text-slate-300 transition-colors hover:text-white"
            >
              <span className="source-provider">{getProviderLabel(normalized.provider)}</span>
              <span className="min-w-0 break-words">{normalized.title}</span>
            </a>
            )
          })}
        </div>
      )}
    </div>
  )
}


export default function AgentMessage({ item }) {
  const config = AGENT_CONFIG[item.agent] || AGENT_CONFIG.host
  const presentation = getAgentPresentation(item.agent)
  const align = alignmentClass(config.align)
  const isJudgeVerdict = item.type === 'judge_verdict'
  const isSearch = item.type === 'search_started' || item.type === 'search_complete'
  const isSystemError = item.type === 'system_error'

  if (isSearch) {
    return <SearchCard item={item} config={config} />
  }

  return (
    <div className={`${align} ${isJudgeVerdict ? 'max-w-4xl' : 'max-w-3xl'} min-w-0 w-full animate-fade-in`}>
      <div className={`feed-card ${isJudgeVerdict ? 'feed-card-judge' : ''} ${isSystemError ? 'feed-card-error' : ''} border ${config.borderClass}`}>
        <div className="feed-meta">
          <AgentIcon agent={item.agent === 'system' ? 'judge' : item.agent} size={14} className={config.colorClass} />
          <span className={config.colorClass}>{presentation.name}</span>
          <span className="text-slate-500">{presentation.role}</span>
        </div>
        <p className={`mt-3 break-words leading-relaxed ${item.agent === 'crowd' ? 'text-arena-crowd italic' : 'text-slate-100'} ${isJudgeVerdict ? 'verdict-text' : ''}`}>
          {item.message}
        </p>
      </div>
    </div>
  )
}
