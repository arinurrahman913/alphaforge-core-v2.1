import { useState } from 'react'
import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import HBarChart from '../components/HBarChart'
import Layer1ComponentModal from '../components/Layer1ComponentModal'
import StatDetailModal from '../components/StatDetailModal'
import Sparkline, { InputBar } from '../components/Sparkline'
import Icon from '../components/Icon'
import { describeComponent, deltaArrow, componentIcon } from '../layer1meta'

export default function Layer1View() {
  const { data, error } = useStageData(api.layer1)
  const [selected, setSelected] = useState(null)
  const [statDetail, setStatDetail] = useState(null)

  if (error) return <div className="empty">Gagal memuat data/layer1_context.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const comps = data.components || {}
  const entries = Object.entries(comps)
  const ok = entries.filter(([, c]) => c.status === 'ok').length
  const deg = entries.length - ok
  const layerScore = data.layer_score

  const stats = [
    { label: 'Layer Score', value: layerScore ? layerScore.final_score.toFixed(0) : '—', icon: 'gauge', accent: '#e8b84b', onClick: () => setStatDetail('score') },
    { label: 'Komponen', value: entries.length, icon: 'layers', accent: '#818CF8', onClick: () => setStatDetail('components') },
    { label: 'OK', value: ok, tone: 'good', icon: 'check', accent: '#4ADE80', onClick: () => setStatDetail('ok') },
    { label: 'Degraded', value: deg, tone: deg ? 'warn' : undefined, icon: 'alert', accent: '#FBBF7A', onClick: () => setStatDetail('degraded') },
    { label: 'Confidence', value: `${data.context_summary?.confidence?.score?.toFixed(0) ?? '—'}%`, icon: 'shield', accent: '#22D3EE', onClick: () => setStatDetail('confidence') },
  ]

  const contribChart = layerScore
    ? [...layerScore.contributions]
        .sort((a, b) => b.weighted - a.weighted)
        .map((c) => ({ label: c.component, count: Math.round(c.weighted * 10) / 10, color: 'linear-gradient(90deg,#e8b84b,#f5cf6f)' }))
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

      <div className="l1a-grid">
        {entries.map(([key, c], idx) => {
          const m = describeComponent(key, c)
          const isDeg = c.status !== 'ok'
          const chartColor = isDeg ? '#4fd1e0' : '#e8b84b'
          return (
            <div className={`l1a-card${isDeg ? ' deg' : ''}`} key={key} onClick={() => setSelected(c)} style={{ '--i': idx }}>
              <div className="l1a-top">
                <div className="l1a-idwrap">
                  <span className={`l1a-ic${isDeg ? ' cy' : ''}`}>
                    <Icon name={componentIcon(key)} size={18} />
                  </span>
                  <div>
                    <p className="l1a-label">{c.name || key}</p>
                    <div className="l1a-val">
                      {m.hero}
                      {m.unit && <span className="u">{m.unit}</span>}
                    </div>
                  </div>
                </div>
                <span className={`l1a-pill ${isDeg ? 'dg' : 'ok'}`}>{isDeg ? 'degraded' : 'ok'}</span>
              </div>
              {m.delta && <span className={`l1a-delta ${m.delta.dir}`}>{deltaArrow(m.delta.dir)} {m.delta.text}</span>}

              {m.stats && (
                <div className="l1a-mini">
                  {m.stats.map((s, i) => (
                    <div key={i}>
                      <p className="l1a-mini-l">{s.l}</p>
                      <p className="l1a-mini-v">{s.v}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="l1a-chart">
                {key === 'market_sentiment' ? (
                  <InputBar used={m.inputsUsed ?? 1} total={4} color={chartColor} />
                ) : (
                  <Sparkline trend={m.trend} color={chartColor} seed={key} height={m.stats ? 36 : 52} />
                )}
              </div>

              <p className="l1a-foot">{c.narrative || c.note || '—'}</p>
              <div className="l1a-meta">
                {c.confidence !== null && c.confidence !== undefined && <span>conf {c.confidence.toFixed(0)}%</span>}
                {c.data_freshness && <span>· {c.data_freshness}</span>}
                {c.conflicts?.length > 0 && <span className="cf">· {c.conflicts.length} konflik</span>}
              </div>
            </div>
          )
        })}
      </div>

      {selected && <Layer1ComponentModal component={selected} onClose={() => setSelected(null)} />}
      {statDetail && <StatDetailModal which={statDetail} data={data} onClose={() => setStatDetail(null)} />}
    </>
  )
}
