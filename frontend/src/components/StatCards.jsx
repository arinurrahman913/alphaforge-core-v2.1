// stats: [{ label, value, tone? }] — tone is 'good' | 'warn' | 'bad' | undefined
export default function StatCards({ stats }) {
  return (
    <div className="stats">
      {stats.map((s) => (
        <div className="stat" key={s.label}>
          <div className="stat-label">{s.label}</div>
          <div className={`stat-value${s.tone ? ' ' + s.tone : ''}`}>{s.value}</div>
        </div>
      ))}
    </div>
  )
}
