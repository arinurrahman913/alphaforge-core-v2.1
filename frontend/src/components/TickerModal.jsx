import { useEffect, useState } from 'react'
import { api } from '../api'
import { fmtPct, fmtMoney, ratingClass } from '../format'

export default function TickerModal({ ticker, onClose }) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [live, setLive] = useState(null) // null = loading, {stale:true} = failed, else fresh quote

  useEffect(() => {
    let cancelled = false
    setData(null)
    setError(null)
    api
      .ticker(ticker)
      .then((d) => {
        if (!cancelled) setData(d)
      })
      .catch((e) => {
        if (!cancelled) setError(String(e))
      })
    return () => {
      cancelled = true
    }
  }, [ticker])

  useEffect(() => {
    let cancelled = false
    setLive(null)
    // Independent from the main fetch above — this one can be slow (live
    // Yahoo lookup) or fail without blocking the rest of the modal.
    api
      .liveQuote(ticker)
      .then((d) => {
        if (!cancelled) setLive(d)
      })
      .catch((e) => {
        if (!cancelled) setLive({ stale: true, error: String(e) })
      })
    return () => {
      cancelled = true
    }
  }, [ticker])

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="modal" onClick={(e) => e.target.classList.contains('modal') && onClose()}>
      <div className="modal-box">
        <div className="modal-head">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h2>{ticker}</h2>
            <LiveQuoteBadge live={live} />
          </div>
          <button className="x" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="modal-body">
          {error && <div className="empty">Gagal memuat detail: {error}</div>}
          {!error && !data && <div className="loading">Memuat detail…</div>}
          {data && <ModalBody data={data} />}
        </div>
      </div>
    </div>
  )
}

function LiveQuoteBadge({ live }) {
  if (!live) {
    return <span className="pill neutral">live …</span>
  }
  if (live.stale || live.last_price === undefined || live.last_price === null) {
    return <span className="pill neutral" title={live.error || 'live quote unavailable'}>live n/a</span>
  }
  const tone = live.change_pct >= 0 ? 'ok' : 'bad'
  return (
    <span className={`pill ${tone}`} title={`fetched ${live.fetched_at}`}>
      ${live.last_price.toFixed(2)} {fmtPct(live.change_pct)}
    </span>
  )
}

function ModalBody({ data }) {
  const { aggregator, reasoning, risk, confidence, knowledge, evidence, historical } = data
  const anySection = aggregator || reasoning || risk?.red_flags?.length || confidence || knowledge || evidence || historical

  if (!anySection) return <div className="empty">Tidak ada detail untuk ticker ini.</div>

  return (
    <>
      {aggregator && (
        <>
          <div className="mrow">
            <div className="mcell">
              <div className="mcell-label">Recommendation</div>
              <div className="mcell-val">
                <span className={`pill ${ratingClass(aggregator.recommendation)}`}>
                  {aggregator.recommendation.replace('_', ' ')}
                </span>
              </div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Conviction</div>
              <div className="mcell-val">{aggregator.conviction}%</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Confidence</div>
              <div className="mcell-val">{aggregator.confidence_score.toFixed(0)}</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Risk Score</div>
              <div className="mcell-val">{aggregator.risk_score.toFixed(0)}</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Reasoning</div>
              <div className="mcell-val">{aggregator.reasoning_score.toFixed(0)}</div>
            </div>
          </div>
          <div className="msection">
            <div className="msection-title">Bull / Bear Case</div>
            <p className="narrative">
              <strong>Bull:</strong> {aggregator.bull_case}
            </p>
            <p className="narrative" style={{ marginTop: 6 }}>
              <strong>Bear:</strong> {aggregator.bear_case}
            </p>
          </div>
          {aggregator.red_flags?.length > 0 && (
            <div className="msection">
              <div className="msection-title">Red Flags</div>
              {aggregator.red_flags.map((f, i) => (
                <div className="flag" key={i}>
                  {f}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {reasoning && (
        <div className="msection">
          <div className="msection-title">Reasoning — 3 Lensa</div>
          {[
            ['quality_output', 'Quality'],
            ['speculative_output', 'Speculative'],
            ['multibagger_output', 'Multibagger'],
          ].map(([key, label]) => {
            const o = reasoning[key]
            if (!o) return null
            return (
              <div className="lens-box" key={key}>
                <div className="lens-head">
                  <span>{label}</span>
                  <span>
                    {o.conviction_score.toFixed(0)} · {o.stance}
                  </span>
                </div>
                {(o.positive_factors || []).map((f, i) => (
                  <div className="factor pos" key={`p${i}`}>
                    + {f}
                  </div>
                ))}
                {(o.negative_factors || []).map((f, i) => (
                  <div className="factor neg" key={`n${i}`}>
                    − {f}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}

      {risk?.red_flags?.length > 0 && (
        <div className="msection">
          <div className="msection-title">
            Risk Detail ({risk.red_flags.length} flags, score {risk.risk_score.toFixed(0)})
          </div>
          {risk.red_flags.map((f, i) => (
            <div className={`flag${f.severity === 'medium' ? ' medium' : ''}`} key={i}>
              <strong>{f.flag_type}</strong> ({f.severity}) — {f.description}
            </div>
          ))}
        </div>
      )}

      {confidence && (
        <div className="msection">
          <div className="msection-title">Confidence Breakdown (overall {confidence.overall_confidence.toFixed(0)}%)</div>
          <div className="mrow">
            <div className="mcell">
              <div className="mcell-label">Price</div>
              <div className="mcell-val">{confidence.price_data_confidence.toFixed(0)}%</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Fundamentals</div>
              <div className="mcell-val">{confidence.fundamental_data_confidence.toFixed(0)}%</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Ownership</div>
              <div className="mcell-val">{confidence.ownership_data_confidence.toFixed(0)}%</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Governance</div>
              <div className="mcell-val">{confidence.governance_data_confidence.toFixed(0)}%</div>
            </div>
          </div>
          <p className="narrative">{confidence.confidence_notes || ''}</p>
        </div>
      )}

      {knowledge && (
        <div className="msection">
          <div className="msection-title">Knowledge — Revenue Trend (YoY)</div>
          <div className="mrow">
            {['yoy_q1', 'yoy_q2', 'yoy_q3', 'yoy_q4'].map((k, i) => (
              <div className="mcell" key={k}>
                <div className="mcell-label">{i === 3 ? 'Q terkini' : `Q-${3 - i}`}</div>
                <div className="mcell-val">{fmtPct(knowledge.financial_health?.revenue_trend?.[k])}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {evidence && (
        <div className="msection">
          <div className="msection-title">Evidence — Sumber Data</div>
          <div className="mrow">
            <div className="mcell">
              <div className="mcell-label">Price Source</div>
              <div className="mcell-val" style={{ fontSize: 12 }}>
                {evidence.price_market?.metadata?.source || '—'}
              </div>
            </div>
            <div className="mcell">
              <div className="mcell-label">SEC Filings</div>
              <div className="mcell-val" style={{ fontSize: 12 }}>
                {evidence.sec_filings?.items?.length || 0} filing(s)
              </div>
            </div>
            <div className="mcell">
              <div className="mcell-label">SEC Quarterly</div>
              <div className="mcell-val" style={{ fontSize: 12 }}>
                {evidence.fundamental?.quarterly_data?.length || 0} kuartal
              </div>
            </div>
            <div className="mcell">
              <div className="mcell-label">News</div>
              <div className="mcell-val" style={{ fontSize: 12 }}>
                {evidence.news?.news?.length || 0} artikel
              </div>
            </div>
          </div>
        </div>
      )}

      {evidence?.institutional_ownership && (
        <InstitutionalHoldersSection ownership={evidence.institutional_ownership} />
      )}

      {historical && (
        <div className="msection">
          <div className="msection-title">
            Historical Tracking (accuracy {historical.accuracy_pct !== null && historical.accuracy_pct !== undefined ? historical.accuracy_pct.toFixed(0) + '%' : '—'})
          </div>
          {historical.records.map((r, i) => (
            <div className="lens-box" key={i}>
              <div className="lens-head">
                <span>
                  {r.recommendation} @ {r.recommendation_date.slice(0, 10)}
                </span>
                <span>{r.actual_return_pct !== null && r.actual_return_pct !== undefined ? fmtPct(r.actual_return_pct) : 'pending'}</span>
              </div>
              <div className="factor" style={{ color: 'var(--dim)' }}>
                {r.reasoning_summary}
              </div>
              {r.decision_correct !== null && r.decision_correct !== undefined && (
                <div className={`factor ${r.decision_correct ? 'pos' : 'neg'}`}>
                  {r.decision_correct ? '✓ Prediksi benar' : '✗ Prediksi meleset'}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  )
}

const ID_MONTHS = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

function fmtIdDate(d) {
  return `${d.getUTCDate()} ${ID_MONTHS[d.getUTCMonth()]} ${d.getUTCFullYear()}`
}

// 13F wajib dilaporkan institusi (>$100M AUM) paling lambat 45 hari setelah
// kuartal tutup — jadi data kuartal berjalan belum akan ADA di manapun
// (SEC, Yahoo, siapapun) sampai deadline itu lewat, bukan soal cache basi
// di sisi kita. dateReportedStr = tanggal akhir kuartal yang datanya kita
// punya (mis. "2026-03-31"); fungsi ini hitung kapan kuartal BERIKUTNYA
// wajib dilaporkan.
function nextFilingDeadline(dateReportedStr) {
  const d = new Date(dateReportedStr + 'T00:00:00Z')
  if (isNaN(d.getTime())) return null
  // Date.UTC(year, month+4, 0) = hari terakhir bulan (month+3) — cara aman
  // hitung "3 bulan lagi, akhir bulan" tanpa overflow kalau tanggal asal
  // (mis. 31) tidak ada di bulan target (mis. Maret 31 -> Juni cuma 30 hari,
  // setUTCMonth naif akan overflow diam-diam ke 1 Juli).
  const nextQuarterEnd = new Date(Date.UTC(d.getUTCFullYear(), d.getUTCMonth() + 4, 0))
  const deadline = new Date(nextQuarterEnd)
  deadline.setUTCDate(deadline.getUTCDate() + 45)
  return deadline
}

// Yahoo pakai pct_change=100.0 sebagai sentinel "posisi baru" (nggak bisa
// hitung % kenaikan dari basis 0 saham sebelumnya) — bukan literal "naik
// 100%" dari posisi lama.
function holderSignal(pctChange) {
  if (pctChange === null || pctChange === undefined) return { label: '—', tone: 'neutral' }
  if (pctChange >= 99.5) return { label: '🆕 Baru Masuk', tone: 'good' }
  if (pctChange > 0) return { label: `▲ +${pctChange.toFixed(1)}%`, tone: 'good' }
  if (pctChange < 0) return { label: `▼ ${pctChange.toFixed(1)}%`, tone: 'bad' }
  return { label: '— Tetap', tone: 'neutral' }
}

function InstitutionalHoldersSection({ ownership }) {
  const holders = ownership.top_holders || []
  const pct = ownership.percentage

  if ((pct === null || pct === undefined) && holders.length === 0) return null

  // Urutkan: posisi baru/nambah paling banyak duluan — lebih actionable
  // daripada urutan default Yahoo (yang cuma berdasar % kepemilikan).
  const sorted = [...holders].sort((a, b) => (b.pct_change ?? -Infinity) - (a.pct_change ?? -Infinity))
  const newCount = holders.filter((h) => h.pct_change >= 99.5).length
  const addedCount = holders.filter((h) => h.pct_change > 0 && h.pct_change < 99.5).length
  const reducedCount = holders.filter((h) => h.pct_change < 0).length

  const latestReportDate = holders.find((h) => h.date_reported)?.date_reported
  const deadline = latestReportDate ? nextFilingDeadline(latestReportDate) : null

  return (
    <div className="msection">
      <div className="msection-title">
        Institutional Holders
        {pct !== null && pct !== undefined && ` — ${(pct * 100).toFixed(1)}% dari total saham dipegang institusi`}
      </div>
      {holders.length === 0 ? (
        <p className="narrative">Detail per-institusi tidak tersedia (data mentah dari Yahoo Finance).</p>
      ) : (
        <>
          {deadline && (
            <p className="narrative" style={{ fontSize: 11, color: 'var(--faint)', marginBottom: 8 }}>
              Data 13F per {fmtIdDate(new Date(latestReportDate + 'T00:00:00Z'))} — ini yang terbaru tersedia di manapun (SEC, Yahoo, dll).
              13F wajib dilaporkan institusi maks. 45 hari setelah kuartal tutup, jadi kuartal berikutnya baru akan muncul
              sekitar {fmtIdDate(deadline)}, bukan karena data kita basi.
            </p>
          )}
          <p className="narrative" style={{ marginBottom: 10 }}>
            {newCount > 0 && <span style={{ color: 'var(--good)' }}>{newCount} institusi baru masuk</span>}
            {newCount > 0 && (addedCount > 0 || reducedCount > 0) && ' · '}
            {addedCount > 0 && <span style={{ color: 'var(--good)' }}>{addedCount} nambah posisi</span>}
            {addedCount > 0 && reducedCount > 0 && ' · '}
            {reducedCount > 0 && <span style={{ color: 'var(--bad)' }}>{reducedCount} kurangi posisi</span>}
            {newCount === 0 && addedCount === 0 && reducedCount === 0 && 'Tidak ada perubahan posisi signifikan dari laporan sebelumnya.'}
            {' '}(dari {holders.length} institusi terbesar, laporan 13F kuartalan terakhir)
          </p>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontFamily: 'var(--sans)', fontSize: 12.5 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--rule)', color: 'var(--faint)', textAlign: 'left' }}>
                <th style={{ padding: '4px 8px 8px 0', fontWeight: 600 }}>Institusi</th>
                <th style={{ padding: '4px 8px 8px', fontWeight: 600, textAlign: 'right' }}>% Held</th>
                <th style={{ padding: '4px 8px 8px', fontWeight: 600, textAlign: 'right' }}>Shares</th>
                <th style={{ padding: '4px 8px 8px', fontWeight: 600, textAlign: 'right' }}>Value</th>
                <th style={{ padding: '4px 8px 8px', fontWeight: 600, textAlign: 'right' }}>Aktivitas</th>
                <th style={{ padding: '4px 0 8px 8px', fontWeight: 600, textAlign: 'right' }}>Dilaporkan</th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((h, i) => {
                const signal = holderSignal(h.pct_change)
                const toneColor = signal.tone === 'good' ? 'var(--good)' : signal.tone === 'bad' ? 'var(--bad)' : 'var(--dim)'
                return (
                  <tr key={i} style={{ borderBottom: '1px solid var(--rule)' }}>
                    <td style={{ padding: '6px 8px 6px 0' }}>{h.holder}</td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontFamily: 'var(--mono)' }}>
                      {h.pct_held !== null && h.pct_held !== undefined ? `${h.pct_held.toFixed(2)}%` : '—'}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontFamily: 'var(--mono)' }}>
                      {h.shares !== null && h.shares !== undefined ? h.shares.toLocaleString() : '—'}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontFamily: 'var(--mono)' }}>{fmtMoney(h.value_usd)}</td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', fontFamily: 'var(--mono)', fontWeight: 600, color: toneColor }}>
                      {signal.label}
                    </td>
                    <td style={{ padding: '6px 0 6px 8px', textAlign: 'right', color: 'var(--faint)', fontSize: 11 }}>
                      {h.date_reported || '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}
