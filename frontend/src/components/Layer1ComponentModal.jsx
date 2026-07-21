import { useEffect } from 'react'
import { ratingClass, prettyLabel } from '../format'
import { describeComponent, deltaArrow, interpretationOf } from '../layer1meta'

const FRESHNESS_TONE = { fresh: 'ok', acceptable: 'warn', stale: 'bad' }

export default function Layer1ComponentModal({ component, onClose }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!component) return null
  const c = component
  const m = describeComponent(c._key || c.name, c)
  const interp = interpretationOf(c)
  const scoreVal = c.contribution ? c.contribution.score : c.raw_score

  return (
    <div className="modal" onClick={(e) => e.target.classList.contains('modal') && onClose()}>
      <div className="modal-box">
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h2>{prettyLabel(c.name)}</h2>
            <span className={`pill ${ratingClass(c.status)}`}>{c.status}</span>
          </div>
          <button className="x" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="modal-body">
          <div className="l1sum">
            <div className="l1sum-grid">
              <div className="l1sum-cell">
                <div className="l1sum-l">Result</div>
                <div className="l1sum-v">
                  {m.hero}
                  {m.unit && <span className="l1sum-u"> {m.unit}</span>}
                </div>
                {m.delta && <div className={`l1sum-delta ${m.delta.dir}`}>{deltaArrow(m.delta.dir)} {m.delta.text}</div>}
              </div>
              <div className="l1sum-cell">
                <div className="l1sum-l">Score (raw)</div>
                <div className="l1sum-v">{scoreVal != null ? scoreVal.toFixed(0) : '—'}<span className="l1sum-u"> /100</span></div>
              </div>
              <div className="l1sum-cell">
                <div className="l1sum-l">Contribution</div>
                <div className="l1sum-v">
                  {c.contribution ? c.contribution.weighted.toFixed(1) : '—'}
                  {c.contribution && <span className="l1sum-u"> ({(c.contribution.weight * 100).toFixed(0)}%)</span>}
                </div>
              </div>
            </div>
            <div className="l1sum-interp"><span className="l1sum-so">So what?</span> {interp}</div>
          </div>

          {c._key === "market_regime" && c.value?.aggregate_signals && (
            <div className="msection">
              <div className="msection-title">Agregasi Konteks</div>
              <div className="agg-summary">
                <span className="agg-bull">Bullish {c.value.aggregate_summary?.bullish_count ?? 0}</span>
                <span className="agg-neutral">Neutral {c.value.aggregate_summary?.neutral_count ?? 0}</span>
                <span className="agg-bear">Bearish {c.value.aggregate_summary?.bearish_count ?? 0}</span>
              </div>
              <div style={{ marginTop: 12 }}>
                {Object.entries(c.value.aggregate_signals).map(([comp, dir]) => (
                  <div key={comp} className="agg-signal">
                    <span className="agg-comp">{prettyLabel(comp)}</span>
                    <span className={`agg-dir ${dir}`}>{dir}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {c._key === "market_regime" && c.value?.triggers && (
            <div className="msection">
              <div className="msection-title">Apa yang bisa ubah regime ini?</div>
              <ul style={{ paddingLeft: 18, marginTop: 8 }}>
                {c.value.triggers.map((trigger, i) => (
                  <li key={i} className="narrative" style={{ fontSize: 12.5, marginBottom: 6 }}>
                    {trigger}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {c.narrative && (
            <div className="msection">
              <div className="msection-title">Reasoning</div>
              <p className="narrative">{c.narrative}</p>
            </div>
          )}

          <div className="mrow">
            <div className="mcell">
              <div className="mcell-label">Confidence</div>
              <div className="mcell-val">{c.confidence !== null && c.confidence !== undefined ? `${c.confidence.toFixed(0)}%` : '—'}</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Data Freshness</div>
              <div className="mcell-val">
                {c.data_freshness ? (
                  <span className={`pill ${FRESHNESS_TONE[c.data_freshness] || 'neutral'}`}>{c.data_freshness}</span>
                ) : (
                  '—'
                )}
              </div>
            </div>
            {c.method_version && (
              <div className="mcell">
                <div className="mcell-label">Method Version</div>
                <div className="mcell-val" style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{c.method_version}</div>
              </div>
            )}
          </div>

          {c.rule && (
            <div className="msection">
              <div className="msection-title">Rule</div>
              <p className="narrative" style={{ fontFamily: 'var(--mono)', fontSize: 12.5 }}>
                {c.rule}
              </p>
            </div>
          )}

          {c.thresholds?.length > 0 && (
            <div className="msection">
              <div className="msection-title">Thresholds</div>
              {c.thresholds.map((t, i) => (
                <div className="factor" key={i} style={{ fontFamily: 'var(--mono)' }}>
                  {t.label} {t.operator} {t.value}
                </div>
              ))}
            </div>
          )}

          {c.evidence?.length > 0 && (
            <div className="msection">
              <div className="msection-title">Evidence ({c.evidence.length})</div>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Value</th>
                      <th>As Of</th>
                      <th>Source</th>
                    </tr>
                  </thead>
                  <tbody>
                    {c.evidence.map((e, i) => (
                      <tr key={i} style={{ cursor: 'default' }}>
                        <td className="ticker">{prettyLabel(e.field)}</td>
                        <td>{String(e.value)}</td>
                        <td>{e.as_of}</td>
                        <td style={{ whiteSpace: 'normal' }}>{e.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {c.conflicts?.length > 0 && (
            <div className="msection">
              <div className="msection-title">Conflict Check</div>
              {c.conflicts.map((conflict, i) => (
                <div className="flag medium" key={i}>
                  {conflict}
                </div>
              ))}
            </div>
          )}

          {c.note && (
            <div className="msection">
              <div className="msection-title">Note</div>
              <p className="narrative">{c.note}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
