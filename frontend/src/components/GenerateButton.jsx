import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import Icon from './Icon'

const MODES = [
  { key: 'layer1', label: 'Refresh Layer 1', note: '~1 menit · komponen makro (breadth pakai cache terakhir)' },
  { key: 'full', label: 'Full Pipeline', note: 'semua stage · lebih lama' },
]

const fmtTime = (s) => `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`

export default function GenerateButton() {
  const [open, setOpen] = useState(false)
  const [running, setRunning] = useState(false)
  const [mode, setMode] = useState(null)
  const [elapsed, setElapsed] = useState(0)
  const [result, setResult] = useState(null) // { ok, message }
  const pollRef = useRef(null)
  const timerRef = useRef(null)
  const startRef = useRef(0)

  function stopTimers() {
    clearInterval(pollRef.current)
    clearInterval(timerRef.current)
  }

  function beginTracking(m, startedAtMs) {
    setRunning(true)
    setMode(m)
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
        if (s?.running) beginTracking(s.mode, s.started_at ? s.started_at * 1000 : Date.now())
      })
      .catch(() => {})
    return stopTimers
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function start(m) {
    setOpen(false)
    setResult(null)
    const resp = await api.refresh(m).catch(() => ({ error: 'gagal konek ke backend' }))
    if (resp?.error) {
      setResult({ ok: false, message: resp.error })
      return
    }
    beginTracking(m, Date.now())
  }

  if (running) {
    return (
      <div className="gen">
        <button className="gen-btn running" disabled>
          <span className="gen-spin" />
          Generating{mode === 'full' ? ' (full)' : ''}… {fmtTime(elapsed)}
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
      {open && (
        <div className="gen-menu">
          {MODES.map((m) => (
            <button key={m.key} className="gen-item" onClick={() => start(m.key)}>
              <span className="gen-item-l">{m.label}</span>
              <span className="gen-item-n">{m.note}</span>
            </button>
          ))}
        </div>
      )}
      {result && (
        <div className={`gen-result ${result.ok ? 'ok' : 'bad'}`} onClick={() => setResult(null)}>
          {result.ok ? '✓ ' : '✕ '}
          {result.message}
        </div>
      )}
    </div>
  )
}
