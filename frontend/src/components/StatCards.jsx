import Icon from './Icon'

// stats: [{ label, value, tone?, icon?, accent? }]
// tone: 'good' | 'warn' | 'bad' | undefined ; icon: Icon name ; accent: css color for icon badge
export default function StatCards({ stats }) {
  return (
    <div className="stats">
      {stats.map((s) => (
        <div className="stat" key={s.label}>
          {s.icon && (
            <span className="stat-ic" style={s.accent ? { color: s.accent, background: `${s.accent}1f` } : undefined}>
              <Icon name={s.icon} size={17} />
            </span>
          )}
          <div className="stat-label">{s.label}</div>
          <div className={`stat-value${s.tone ? ' ' + s.tone : ''}`}>{s.value}</div>
        </div>
      ))}
    </div>
  )
}
