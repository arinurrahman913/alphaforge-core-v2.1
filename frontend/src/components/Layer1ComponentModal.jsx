import { useEffect } from 'react'
import { ratingClass } from '../format'

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

  return (
    <div className="modal" onClick={(e) => e.target.classList.contains('modal') && onClose()}>
      <div className="modal-box">
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h2>{c.name}</h2>
            <span className={`pill ${ratingClass(c.status)}`}>{c.status}</span>
          </div>
          <button className="x" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="modal-body">
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
            {c.contribution && (
              <>
                <div className="mcell">
                  <div className="mcell-label">Score (raw)</div>
                  <div className="mcell-val">{c.contribution.score.toFixed(0)}</div>
                </div>
                <div className="mcell">
                  <div className="mcell-label">Weight → Weighted</div>
                  <div className="mcell-val">
                    {(c.contribution.weight * 100).toFixed(0)}% → {c.contribution.weighted.toFixed(1)}
                  </div>
                </div>
              </>
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
                        <td className="ticker">{e.field}</td>
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
