import { useState } from 'react'
import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import HBarChart from '../components/HBarChart'
import Layer1ComponentModal from '../components/Layer1ComponentModal'
import { ratingClass } from '../format'

export default function Layer1View() {
  const { data, error } = useStageData(api.layer1)
  const [selected, setSelected] = useState(null)

  if (error) return <div className="empty">Gagal memuat data/layer1_context.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const comps = data.components || {}
  const entries = Object.entries(comps)
  const ok = entries.filter(([, c]) => c.status === 'ok').length
  const deg = entries.length - ok
  const layerScore = data.layer_score

  const stats = [
    { label: 'Layer Score', value: layerScore ? layerScore.final_score.toFixed(0) : '—' },
    { label: 'Komponen', value: entries.length },
    { label: 'OK', value: ok, tone: 'good' },
    { label: 'Degraded', value: deg, tone: deg ? 'warn' : undefined },
    { label: 'Confidence', value: `${data.context_summary?.confidence?.score?.toFixed(0) ?? '—'}%` },
  ]

  const contribChart = layerScore
    ? [...layerScore.contributions]
        .sort((a, b) => b.weighted - a.weighted)
        .map((c) => ({ label: c.component, count: Math.round(c.weighted * 10) / 10, color: 'var(--accent2)' }))
    : []

  const reasons = data.context_summary?.confidence?.reasons || []

  return (
    <>
      <StatCards stats={stats} />

      {layerScore && contribChart.length > 0 && (
        <div className="chart-row">
          <HBarChart title={`Kontribusi ke Layer Score (${layerScore.reasoning})`} data={contribChart} />
        </div>
      )}

      {data.context_summary && (
        <div className="l1-card l1-summary">
          <div className="l1-name">Ringkasan</div>
          <div className="narrative">{data.context_summary.narrative}</div>
          {reasons.length > 0 && (
            <ul style={{ marginTop: 10, paddingLeft: 18 }}>
              {reasons.map((r, i) => (
                <li key={i} className="narrative" style={{ fontSize: 12.5, opacity: 0.85 }}>
                  {r}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="l1-grid">
        {entries.map(([key, c]) => (
          <div className={`l1-card${c.status !== 'ok' ? ' deg' : ''}`} key={key} onClick={() => setSelected(c)} style={{ cursor: 'pointer' }}>
            <div className="l1-name">
              <span>{c.name || key}</span>
              <span className={`pill ${ratingClass(c.status)}`}>{c.status}</span>
            </div>
            <div className="l1-narr">{c.narrative || c.note || '—'}</div>
            {c.confidence !== null && c.confidence !== undefined && (
              <div style={{ marginTop: 8, fontSize: 11, color: 'var(--faint)' }}>
                confidence {c.confidence.toFixed(0)}% · {c.data_freshness || '—'}
                {c.conflicts?.length > 0 && ` · ${c.conflicts.length} konflik`}
              </div>
            )}
          </div>
        ))}
      </div>

      {selected && <Layer1ComponentModal component={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
