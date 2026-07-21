import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'

const MODES = [
  { key: 'layer1', label: 'Refresh Layer 1', note: '~1 menit · komponen makro (breadth pakai cache terakhir)' },
  { key: 'full', label: 'Full Pipeline — Semua Sektor', note: '~1.5-2 jam · seluruh universe (~5.000+ ticker)' },
]

const fmtTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

export default function GenerateButton() {
  const [open, setOpen] = useState(false)
  const [view, setView] = useState('main') // 'main' | 'sectors'
  const [sectorInfo, setSectorInfo] = useState(null)
  const [running, setRunning] = useState(false)
  const [mode, setMode] = useState(null)
  const [sector, setSector] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [result, setResult] = useState(null) // { ok, message }
  const pollRef = useRef(null)
  const timerRef = useRef(null)
  const startRef = useRef(0)

  function stopTimers() {
    clearInterval(pollRef.current)
    clearInterval(timerRef.current)
  }

  function beginTracking(m, startedAtMs, s) {
    setRunning(true)
    setMode(m)
    setSector(s || null)
    startRef.current = startedAtMs
    setElapsed(Math.floor((Date.now() - startedAtMs) / 1000))
    timerRef.current = setInterval(() => setElapsed(Math.floor((Date.now() - startRef.current) / 1000)), 1000)
    pollRef.current = setInterval(poll, 2500)
  }

  async function poll() {
    const s = await api.refreshStatus().catch(() => null)
    if (!s || s.running) return
    stopTimers()
    setRunning(false)
    setResult({ ok: s.ok, message: s.message })
    if (s.ok) setTimeout(() => window.location.reload(), 1300)
  }

  // Resync kalau halaman dibuka saat refresh sedang berjalan (proses ini).
  useEffect(() => {
    api
      .refreshStatus()
      .then((s) => {
        if (s?.running) beginTracking(s.mode, s.started_at ? s.started_at * 1000 : Date.now(), s.sector)
      })
      .catch(() => {})
    return stopTimers
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function start(m, s) {
    setOpen(false)
    setResult(null)
    const resp = await api.refresh(m, s).catch(() => ({ error: 'gagal konek ke backend' }))
    if (resp?.error) {
      setResult({ ok: false, message: resp.error })
      return
    }
    beginTracking(m, Date.now(), s)
  }

  function openSectorMenu() {
    setView('sectors')
    if (!sectorInfo) {
      api.sectors().then(setSectorInfo).catch(() => setSectorInfo({ known_sectors: [], map_built: false }))
    }
  }

  function closeMenu() {
    setOpen(false)
    setView('main')
  }

  if (running) {
    return (
      <div className="gen">
        <button className="gen-btn running" disabled>
          <span className="gen-spin" />
          Generating{mode === 'full' ? ' (full)' : ''}{sector ? ` · ${sector}` : ''}… {fmtTime(elapsed)}
        </button>
      </div>
    )
  }

  return (
    <div className="gen">
      <button className="gen-btn" onClick={() => setOpen((o) => !o)}>
        <Icon name="cycle" size={15} />
        Generate
        <span className="gen-caret">▾</span>
      </button>
      {open && view === 'main' && (
        <div className="gen-menu">
          {MODES.map((m) => (
            <button key={m.key} className="gen-item" onClick={() => start(m.key)}>
              <span className="gen-item-l">{m.label}</span>
              <span className="gen-item-n">{m.note}</span>
            </button>
          ))}
          <button className="gen-item" onClick={openSectorMenu}>
            <span className="gen-item-l">Screening per Sektor ›</span>
            <span className="gen-item-n">fokus satu sektor GICS · jauh lebih cepat</span>
          </button>
        </div>
      )}
      {open && view === 'sectors' && (
        <div className="gen-menu gen-menu-sectors">
          <button className="gen-item gen-back" onClick={() => setView('main')}>
            <span className="gen-item-l">‹ Kembali</span>
          </button>
          {!sectorInfo && <div className="gen-item-n" style={{ padding: '8px 10px' }}>Memuat…</div>}
          {sectorInfo && !sectorInfo.map_built && (
            <div className="gen-sector-warn">
              Sector map belum dibangun — jalankan <code>scripts/build_sector_map.py</code> dulu di server,
              kalau tidak semua sektor akan hasilkan 0 kandidat.
            </div>
          )}
          {sectorInfo && sectorInfo.map_built && (
            <div className="gen-item-n" style={{ padding: '2px 10px 8px' }}>
              {sectorInfo.total_mapped?.toLocaleString()} ticker termapping
            </div>
          )}
          {sectorInfo?.known_sectors?.map((s) => (
            <button key={s} className="gen-item gen-item-sector" onClick={() => start('full', s)}>
              <span className="gen-item-l">{s}</span>
              <span className="gen-item-n">{(sectorInfo.coverage?.[s] || 0).toLocaleString()} ticker</span>
            </button>
          ))}
        </div>
      )}
      {open && <div className="gen-backdrop" onClick={closeMenu} />}
      {result && (
        <div className={`gen-result ${result.ok ? 'ok' : 'bad'}`} onClick={() => setResult(null)}>
          {result.ok ? '✓ ' : '✕ '}
          {result.message}
        </div>
      )}
    </div>
  )
}
