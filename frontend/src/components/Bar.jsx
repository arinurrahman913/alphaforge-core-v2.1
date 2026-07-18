import { clampPct } from '../format'

export default function Bar({ pct, tone = '' }) {
  const p = clampPct(pct)
  return (
    <>
      <span className="bar">
        <span className={`bar-fill${tone ? ' ' + tone : ''}`} style={{ width: `${p}%` }} />
      </span>
      <span className="bar-num">{p.toFixed(0)}</span>
    </>
  )
}
