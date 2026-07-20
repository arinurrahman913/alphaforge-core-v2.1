// Tren LayerScore dari waktu ke waktu — dibangun pasca-audit: sebelumnya tiap
// run cuma snapshot titik-waktu, tidak ada cara melihat apakah skor hari ini
// "normal" atau tidak biasa dibanding beberapa minggu terakhir. Data dari
// dashboard/data/layer1_history.json (satu entry/hari, ditulis refresh script).
const W = 640
const H = 108
const PAD_X = 6
const PAD_Y = 14

function fmtDate(iso) {
  // `iso` adalah tanggal kalender polos (YYYY-MM-DD, UTC) dari layer1_history.json.
  // `new Date('YYYY-MM-DD')` di-parse sebagai UTC tengah malam, lalu
  // toLocaleDateString tanpa timeZone eksplisit mengonversi ke zona lokal
  // browser — di zona negatif (mis. Amerika) tanggalnya bisa mundur 1 hari.
  // timeZone:'UTC' memaksa tampilan tetap sama dengan tanggal kalender asli.
  const d = new Date(iso)
  return d.toLocaleDateString('id-ID', { day: '2-digit', month: 'short', timeZone: 'UTC' })
}

export default function Layer1ScoreTrend({ history }) {
  const entries = Array.isArray(history) ? history : []

  if (entries.length < 2) {
    return (
      <div className="chart-card l1-trend">
        <div className="chart-title">Tren Layer Score</div>
        <p className="l1-trend-empty">
          Histori baru mulai dikumpulkan (
          {entries.length === 0 ? 'belum ada data' : '1 hari tercatat'}
          ) — grafik tren muncul setelah beberapa hari refresh berjalan.
        </p>
      </div>
    )
  }

  const vals = entries.map((e) => e.final_score)
  const rawMin = Math.min(...vals)
  const rawMax = Math.max(...vals)
  const span = Math.max(rawMax - rawMin, 6) // hindari garis nyaris datar terlihat aneh
  const min = rawMax - rawMin < 6 ? (rawMin + rawMax) / 2 - 3 : rawMin
  const max = min + span

  const n = entries.length
  const x = (i) => PAD_X + (W - 2 * PAD_X) * (n > 1 ? i / (n - 1) : 0)
  const y = (v) => PAD_Y + (H - 2 * PAD_Y) * (1 - (v - min) / span)

  const line = vals.map((v, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const area = `${line} L${x(n - 1).toFixed(1)},${H} L${x(0).toFixed(1)},${H} Z`

  const first = vals[0]
  const last = vals[n - 1]
  const delta = last - first
  const dir = delta > 1 ? 'up' : delta < -1 ? 'down' : 'flat'
  const deltaColor = dir === 'up' ? 'var(--good)' : dir === 'down' ? 'var(--bad)' : 'var(--gold-hi)'
  const arrow = dir === 'up' ? '▲' : dir === 'down' ? '▼' : '◆'

  return (
    <div className="chart-card l1-trend">
      <div className="chart-title l1-trend-head">
        <span>Tren Layer Score ({n} hari)</span>
        <span className="l1-trend-delta" style={{ color: deltaColor }}>
          {arrow} {delta >= 0 ? '+' : ''}
          {delta.toFixed(1)} vs {fmtDate(entries[0].date)}
        </span>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} preserveAspectRatio="none" style={{ display: 'block' }}>
        <defs>
          <linearGradient id="l1trend-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#e8b84b" stopOpacity="0.3" />
            <stop offset="1" stopColor="#e8b84b" stopOpacity="0" />
          </linearGradient>
        </defs>
        <line x1={PAD_X} y1={H / 2} x2={W - PAD_X} y2={H / 2} stroke="rgba(255,255,255,.06)" strokeDasharray="3 4" />
        <path d={area} fill="url(#l1trend-fill)" />
        <path d={line} fill="none" stroke="#e8b84b" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx={x(n - 1)} cy={y(last)} r="7" fill="#e8b84b" opacity="0.18" />
        <circle cx={x(n - 1)} cy={y(last)} r="3.4" fill="#f5cf6f" />
      </svg>
      <div className="l1-trend-meta">
        <span>min {rawMin.toFixed(0)}</span>
        <span>maks {rawMax.toFixed(0)}</span>
        <span>terkini {last.toFixed(0)} · {fmtDate(entries[n - 1].date)}</span>
      </div>
    </div>
  )
}
