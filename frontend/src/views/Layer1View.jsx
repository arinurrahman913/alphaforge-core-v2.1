import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import { ratingClass } from '../format'

export default function Layer1View() {
  const { data, error } = useStageData(api.layer1)

  if (error) return <div className="empty">Gagal memuat data/layer1_context.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const comps = data.components || {}
  const entries = Object.entries(comps)
  const ok = entries.filter(([, c]) => c.status === 'ok').length
  const deg = entries.length - ok

  const stats = [
    { label: 'Komponen', value: entries.length },
    { label: 'OK', value: ok, tone: 'good' },
    { label: 'Degraded', value: deg, tone: deg ? 'warn' : undefined },
    { label: 'Confidence', value: `${data.context_summary?.confidence?.score?.toFixed(0) ?? '—'}%` },
  ]

  return (
    <>
      <StatCards stats={stats} />
      {data.context_summary && (
        <div className="l1-card l1-summary">
          <div className="l1-name">Ringkasan</div>
          <div className="narrative">{data.context_summary.narrative}</div>
        </div>
      )}
      <div className="l1-grid">
        {entries.map(([key, c]) => (
          <div className={`l1-card${c.status !== 'ok' ? ' deg' : ''}`} key={key}>
            <div className="l1-name">
              <span>{c.name || key}</span>
              <span className={`pill ${ratingClass(c.status)}`}>{c.status}</span>
            </div>
            <div className="l1-narr">{c.narrative || '—'}</div>
          </div>
        ))}
      </div>
    </>
  )
}
