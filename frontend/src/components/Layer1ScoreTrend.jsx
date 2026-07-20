// Tren LayerScore dari waktu ke waktu. Awalnya cuma garis auto-scale tanpa
// konteks; pasca-revisi UX ditambah: rentang 7D/30D/90D, moving average 7
// hari, background 4 zona regime (skala tetap 0-100), dan tooltip per titik
// (skor, driver & drag terbesar, confidence). Data dari
// dashboard/data/layer1_history.json (satu entry/hari, ditulis refresh script).
import { useState } from 'react'
import { prettyLabel } from '../format'

const W = 640
const H = 150
const PAD_Y = 12

const RANGES = [
  { k: 7, label: '7D' },
  { k: 30, label: '30D' },
  { k: 90, label: '90D' },
]

// Zona regime pada skala Layer Score 0-100 (selaras band_label backend).
const BANDS = [
  { from: 65, to: 100, color: 'rgba(74,222,128,.10)', label: 'Risk-On' },
  { from: 50, to: 65, color: 'rgba(232,184,75,.09)', label: 'Neutral Positive' },
  { from: 35, to: 50, color: 'rgba(148,163,184,.07)', label: 'Neutral' },
  { from: 0, to: 35, color: 'rgba(240,119,106,.10)', label: 'Risk-Off' },
]

function fmtDate(iso) {
  // Tanggal kalender polos (UTC) — paksa timeZone UTC agar tak mundur 1 hari di zona negatif.
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short', timeZone: 'UTC' })
}

function movingAvg(vals, w) {
  return vals.map((_, i) => {
    if (i < w - 1) return null
    let s = 0
    for (let j = i - w + 1; j <= i; j++) s += vals[j]
    return s / w
  })
}

export default function Layer1ScoreTrend({ history }) {
  const all = Array.isArray(history) ? history : []
  const [range, setRange] = useState(30)
  const [hover, setHover] = useState(null)

  if (all.length < 2) {
    return (
      <div className="chart-card l1-trend">
        <div className="chart-title">Tren Layer Score</div>
        <p className="l1-trend-empty">
          Histori baru mulai dikumpulkan (
          {all.length === 0 ? 'belum ada data' : '1 hari tercatat'}
          ) — grafik tren muncul setelah beberapa hari refresh berjalan.
        </p>
      </div>
    )
  }

  const entries = all.slice(-range)
  const n = entries.length
  const vals = entries.map((e) => e.final_score)
  const maW = Math.min(7, n)
  const ma7 = movingAvg(vals, maW)

  // Skala-y TETAP 0-100 supaya zona regime bermakna absolut.
  const y = (v) => PAD_Y + (H - 2 * PAD_Y) * (1 - v / 100)
  const xPx = (i) => (n > 1 ? i / (n - 1) : 0) * W
  const xPct = (i) => (n > 1 ? (i / (n - 1)) * 100 : 0)

  const line = vals.map((v, i) => `${i === 0 ? 'M' : 'L'}${xPx(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const area = `${line} L${xPx(n - 1).toFixed(1)},${H} L${xPx(0).toFixed(1)},${H} Z`
  const maPts = ma7.map((v, i) => (v == null ? null : `${xPx(i).toFixed(1)},${y(v).toFixed(1)}`)).filter(Boolean)
  const maLine = maPts.length > 1 ? 'M' + maPts.join(' L') : ''

  const first = vals[0]
  const last = vals[n - 1]
  const delta = last - first
  const dir = delta > 1 ? 'up' : delta < -1 ? 'down' : 'flat'
  const deltaColor = dir === 'up' ? 'var(--good)' : dir === 'down' ? 'var(--bad)' : 'var(--gold-hi)'
  const arrow = dir === 'up' ? '▲' : dir === 'down' ? '▼' : '◆'

  const h = hover != null ? entries[hover] : null

  return (
    <div className="chart-card l1-trend">
      <div className="chart-title l1-trend-head">
        <span>Tren Layer Score</span>
        <div className="l1-trend-ctrl">
          <span className="l1-trend-delta" style={{ color: deltaColor }}>
            {arrow} {delta >= 0 ? '+' : ''}
            {delta.toFixed(1)} vs {fmtDate(entries[0].date)}
          </span>
          <div className="l1-trend-tabs">
            {RANGES.map((r) => (
              <button key={r.k} className={`l1-trend-tab${range === r.k ? ' on' : ''}`} onClick={() => setRange(r.k)}>
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="l1-trend-plot" onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none" style={{ display: 'block' }}>
          <defs>
            <linearGradient id="l1trend-fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#e8b84b" stopOpacity="0.28" />
              <stop offset="1" stopColor="#e8b84b" stopOpacity="0" />
            </linearGradient>
          </defs>
          {BANDS.map((b) => (
            <rect key={b.label} x="0" y={y(b.to)} width={W} height={y(b.from) - y(b.to)} fill={b.color} />
          ))}
          <path d={area} fill="url(#l1trend-fill)" />
          {maLine && <path d={maLine} fill="none" stroke="rgba(120,200,255,.75)" strokeWidth="1.5" strokeDasharray="4 3" strokeLinecap="round" />}
          <path d={line} fill="none" stroke="#e8b84b" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
          {h && <line x1={xPx(hover)} y1={PAD_Y} x2={xPx(hover)} y2={H} stroke="rgba(255,255,255,.25)" strokeWidth="1" />}
          <circle cx={xPx(hover ?? n - 1)} cy={y(vals[hover ?? n - 1])} r="6.5" fill="#e8b84b" opacity="0.18" />
          <circle cx={xPx(hover ?? n - 1)} cy={y(vals[hover ?? n - 1])} r="3.2" fill="#f5cf6f" />
        </svg>

        {/* Zona hover transparan per titik → tooltip */}
        <div className="l1-trend-hovers">
          {entries.map((e, i) => (
            <div
              key={i}
              className="l1-trend-hz"
              style={{ left: `${xPct(i)}%` }}
              onMouseEnter={() => setHover(i)}
            />
          ))}
        </div>

        {h && (
          <div className="l1-trend-tip" style={{ left: `${xPct(hover)}%` }}>
            <div className="l1-trend-tip-date">{fmtDate(h.date)}{h.band_label ? ` · ${h.band_label}` : ''}</div>
            <div className="l1-trend-tip-grid">
              <span>Score</span><b>{h.final_score.toFixed(1)}</b>
              {h.top_driver && (<><span>Driver</span><b>{prettyLabel(h.top_driver.component)}</b></>)}
              {h.top_drag && (<><span>Drag</span><b>{prettyLabel(h.top_drag.component)}</b></>)}
              {h.confidence_score != null && (<><span>Confidence</span><b>{h.confidence_score.toFixed(0)}%</b></>)}
            </div>
          </div>
        )}
      </div>

      <div className="l1-trend-legend">
        <span><i className="ln gold" /> Score</span>
        <span><i className="ln blue" /> MA{maW}</span>
        <span className="l1-trend-legend-sep">{n} hari · skala 0–100</span>
      </div>
    </div>
  )
}
