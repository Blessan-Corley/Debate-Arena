import AgentIcon from './AgentIcon'
import { getAgentPresentation } from '../lib/arenaPresentation'


export default function ThinkingIndicator({ agent }) {
  if (!agent) return null
  const presentation = getAgentPresentation(agent)

  return (
    <div className="max-w-xl mr-auto animate-fade-in">
      <div className="feed-card border border-arena-border">
        <div className="feed-meta">
          <AgentIcon agent={agent} size={14} className={`agent-${agent}`} />
          <span className={`agent-${agent}`}>{presentation.name}</span>
          <span className="text-slate-500">Thinking</span>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <div className="flex gap-1.5">
            <span className="think-dot w-2 h-2 rounded-full bg-arena-host" />
            <span className="think-dot w-2 h-2 rounded-full bg-arena-host" />
            <span className="think-dot w-2 h-2 rounded-full bg-arena-host" />
          </div>
          <p className="text-sm text-slate-300">{presentation.thinking || 'Thinking...'}</p>
        </div>
      </div>
    </div>
  )
}
