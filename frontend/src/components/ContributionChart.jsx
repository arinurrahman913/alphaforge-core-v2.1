import { prettyLabel } from '../format'

// Kontribusi tiap komponen ke Layer Score — horizontal bar, dipisah
// Driver (skor > 50, menarik skor ke atas / Risk-On) vs Drag (skor < 50,
// menekan ke bawah / Risk-Off). Panjang bar = besar kontribusi tertimbang
// (skor × bobot) yang benar-benar masuk ke final_score. Hover → tooltip
// menjelaskan Contribution / Weight / Status / Interpretation.
const GOLD = '#e8b84b'
const RED = '#f0776a'

function interpret(score) {
  if (score >= 55) return { role: 'Driver', text: 'mendorong skor ke atas (condong Risk-On)' }
  if (score <= 45) return { role: 'Drag', text: 'menekan skor ke bawah (condong Risk-Off)' }
  return { role: 'Netral', text: 'kontribusi mendekati netral' }
}

export default function ContributionChart({ contributions, statusByComponent = {} }) {
  const rows = [...contributions].sort((a, b) => b.weighted - a.weighted)
  const max = Math.max(...rows.map((r) => r.weighted), 1)

  return (
    <div className="chart-card">
      <div className="chart-title">Contribution to Layer Score</div>
      <div className="contrib-legend">
        <span><i style={{ background: GOLD }} /> Driver</span>
        <span><i style={{ background: RED }} /> Drag</span>
      </div>
      {rows.map((r) => {
        const meta = interpret(r.score)
        const color = r.score >= 55 ? GOLD : r.score <= 45 ? RED : 'rgba(180,190,210,.55)'
        const status = statusByComponent[r.component] || 'ok'
        return (
          <div className="contrib-row" key={r.component}>
            <div className="contrib-label">{prettyLabel(r.component)}</div>
            <div className="contrib-track">
              <div className="contrib-fill" style={{ width: `${(r.weighted / max) * 100}%`, background: color }} />
            </div>
            <div className="contrib-val">{r.weighted.toFixed(1)}</div>
            <div className="contrib-tip" role="tooltip">
              <div className="contrib-tip-title">
                {prettyLabel(r.component)} · <span style={{ color }}>{meta.role}</span>
              </div>
              <div className="contrib-tip-grid">
                <span>Contribution</span><b>{r.weighted.toFixed(2)}</b>
                <span>Weight</span><b>{(r.weight * 100).toFixed(0)}%</b>
                <span>Score</span><b>{r.score.toFixed(0)} / 100</b>
                <span>Status</span><b>{status}</b>
              </div>
              <div className="contrib-tip-interp">{prettyLabel(r.component)} {meta.text}.</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
