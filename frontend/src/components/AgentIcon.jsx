/**
 * Inline SVG icons for each debate agent.
 * All icons are 14×14, stroke-based, sharp geometric style.
 */
export default function AgentIcon({ agent, size = 14, className = '', style }) {
  const props = {
    width: size,
    height: size,
    viewBox: '0 0 14 14',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.5,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    className,
    style,
    'aria-hidden': true,
  }

  switch (agent) {
    case 'host':
      // Microphone
      return (
        <svg {...props}>
          <rect x="4.5" y="1" width="5" height="7" rx="2.5" />
          <path d="M2 7.5a5 5 0 0010 0" />
          <line x1="7" y1="12.5" x2="7" y2="14" />
          <line x1="4.5" y1="14" x2="9.5" y2="14" />
        </svg>
      )

    case 'pro':
      // Upward arrow — ascending argument
      return (
        <svg {...props}>
          <line x1="7" y1="12" x2="7" y2="3" />
          <polyline points="3.5,6.5 7,3 10.5,6.5" />
        </svg>
      )

    case 'con':
      // Downward arrow — rebuttal
      return (
        <svg {...props}>
          <line x1="7" y1="2" x2="7" y2="11" />
          <polyline points="3.5,7.5 7,11 10.5,7.5" />
        </svg>
      )

    case 'crowd':
      // Soundwave bars — live audience energy
      return (
        <svg {...props} fill="currentColor" stroke="none">
          <rect x="0.5" y="5" width="2" height="4" rx="1" />
          <rect x="3.5" y="3" width="2" height="8" rx="1" />
          <rect x="6.5" y="1" width="2" height="12" rx="1" />
          <rect x="9.5" y="3" width="2" height="8" rx="1" />
          <rect x="12.5" y="5" width="1" height="4" rx="0.5" />
        </svg>
      )

    case 'judge':
      // Scales of justice
      return (
        <svg {...props}>
          <line x1="7" y1="1" x2="7" y2="13" />
          <line x1="3.5" y1="1" x2="10.5" y2="1" />
          <line x1="3.5" y1="1" x2="1.5" y2="5" />
          <line x1="10.5" y1="1" x2="12.5" y2="5" />
          <path d="M1 5a2.5 2.5 0 005 0" />
          <path d="M8 5a2.5 2.5 0 005 0" />
          <line x1="4.5" y1="13" x2="9.5" y2="13" />
        </svg>
      )

    case 'human':
      // Person silhouette
      return (
        <svg {...props}>
          <circle cx="7" cy="4" r="2.5" />
          <path d="M1.5 13.5a5.5 5.5 0 0111 0" />
        </svg>
      )

    default:
      return null
  }
}
