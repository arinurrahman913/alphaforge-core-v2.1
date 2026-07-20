import Icon from './Icon'

// stats: [{ label, value, tone?, icon?, accent?, onClick? }]
// tone: 'good' | 'warn' | 'bad' | undefined ; icon: Icon name ; accent: css color for icon badge
// onClick: kalau ada, tile jadi bisa diklik (buka rincian) + tampil hint
export default function StatCards({ stats }) {
  return (
    <div className="stats">
      {stats.map((s, i) => (
        <div
          className={`stat${s.onClick ? ' stat-click' : ''}`}
          key={s.label}
          onClick={s.onClick}
          role={s.onClick ? 'button' : undefined}
          tabIndex={s.onClick ? 0 : undefined}
          style={{ '--c': s.accent || '#e8b84b', '--i': i }}
        >
          {s.icon && (
            <span className="stat-ic">
              <Icon name={s.icon} size={17} />
            </span>
          )}
          <div className="stat-label">{s.label}</div>
          <div className={`stat-value${s.tone ? ' ' + s.tone : ''}`}>{s.value}</div>
          {s.sub && <div className="stat-sub">{s.sub}</div>}
          {s.onClick && <div className="stat-hint">Lihat perhitungan ›</div>}
        </div>
      ))}
    </div>
  )
}
