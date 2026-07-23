const NAV_GROUPS = [
  { title: 'Market', items: [{ id: 'layer1', label: 'Layer 1 — Context' }] },
  {
    title: 'Fase A — Per Ticker',
    items: [
      { id: 'screening', label: 'Screening' },
      { id: 'evidence', label: 'Evidence' },
      { id: 'knowledge', label: 'Knowledge' },
      { id: 'catalyst', label: 'Catalyst' },
    ],
  },
  {
    title: 'Fase B — Populasi',
    items: [
      { id: 'peer', label: 'Peer Comparison' },
      { id: 'confidence', label: 'Confidence' },
      { id: 'risk', label: 'Risk / Red Flags' },
      { id: 'reasoning', label: 'Reasoning' },
      { id: 'aggregator', label: 'Aggregator' },
    ],
  },
  { title: 'Tracking', items: [{ id: 'historical', label: 'Historical' }] },
]

export default function Sidebar({ activeView, onSelect }) {
  return (
    <div className="sidebar">
      <div className="brand">
        <div className="brand-name">
          AlphaForge <b>v2</b>
        </div>
        <div className="brand-sub">pipeline dashboard · data live</div>
      </div>

      {NAV_GROUPS.map((group) => (
        <div className="nav-group" key={group.title}>
          <div className="nav-group-title">{group.title}</div>
          {group.items.map((item) => (
            <div
              key={item.id}
              className={`nav-item${activeView === item.id ? ' active' : ''}`}
              onClick={() => onSelect(item.id)}
            >
              {item.label}
            </div>
          ))}
        </div>
      ))}
    </div>
  )
}
