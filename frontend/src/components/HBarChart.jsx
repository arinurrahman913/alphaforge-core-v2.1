// Simple horizontal bar chart, pure CSS/SVG-free — data: [{ label, count, color }]
export default function HBarChart({ title, data }) {
  const max = Math.max(...data.map((d) => d.count), 1)

  return (
    <div className="chart-card">
      <div className="chart-title">{title}</div>
      {data.map((d) => (
        <div className="hbar-row" key={d.label}>
          <div className="hbar-label">{d.label}</div>
          <div className="hbar-track">
            <div className="hbar-fill" style={{ width: `${(d.count / max) * 100}%`, background: d.color }} />
          </div>
          <div className="hbar-count">{d.count}</div>
        </div>
      ))}
    </div>
  )
}
