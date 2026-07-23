import { useEffect, useState } from 'react'
import { api } from '../api'
import { fmtPct, fmtMoney, ratingClass, stanceClass, prettyStance, bandClass, prettyLabel, MODULE_LABELS } from '../format'

const MODULES = ['multibagger', 'quality_compound', 'speculative']

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
  const { aggregator, reasoning, risk, confidence, catalyst, knowledge, evidence, historical } = data
  const anySection = aggregator || reasoning || risk || confidence || catalyst || knowledge || evidence || historical

  if (!anySection) return <div className="empty">Tidak ada detail untuk ticker ini.</div>

  const synthesis = aggregator?.synthesis

  return (
    <>
      {aggregator?.halted && (
        <div className="msection">
          <div className="flag">
            <strong>HALTED</strong> — {aggregator.halt_reason || 'red flag severity ekstrem terpicu'}.
            Saham ini tidak diteruskan ke modul reasoning (hard-gate keselamatan).
          </div>
        </div>
      )}

      {synthesis && (
        <div className="msection">
          <div className="msection-title">
            Sintesis — {synthesis.full_convergence ? '3 lensa konvergen' : 'ada perbedaan pandangan'}
          </div>
          <div className="mrow">
            <div className="mcell">
              <div className="mcell-label">Confidence (terendah)</div>
              <div className="mcell-val">
                <span className={`pill ${bandClass(synthesis.confidence?.band)}`}>
                  {synthesis.confidence ? `${synthesis.confidence.score.toFixed(0)} · ${synthesis.confidence.band}` : '—'}
                </span>
              </div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Surprise</div>
              <div className="mcell-val">{synthesis.surprise != null ? synthesis.surprise.toFixed(2) : '—'}</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Kesepakatan</div>
              <div className="mcell-val">{synthesis.agreements?.length ?? 0}</div>
            </div>
            <div className="mcell">
              <div className="mcell-label">Perbedaan</div>
              <div className="mcell-val">{synthesis.divergences?.length ?? 0}</div>
            </div>
          </div>
          {synthesis.narrative && <p className="narrative" style={{ marginTop: 8 }}>{synthesis.narrative}</p>}
          {(synthesis.divergences || []).map((d, i) => (
            <div className="lens-box" key={`div${i}`}>
              <div className="lens-head">
                <span>{d.claim}</span>
                <span style={{ color: 'var(--faint)', fontSize: 11 }}>akar: {d.root_cause}</span>
              </div>
              {(d.modules || []).map((m, j) => (
                <div className="factor" key={j} style={{ color: 'var(--dim)' }}>
                  {MODULE_LABELS[m.module] || m.module}: {m.position}
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {reasoning && !aggregator?.halted && (
        <div className="msection">
          <div className="msection-title">Reasoning — 3 Lensa Independen</div>
          {MODULES.map((key) => {
            const o = reasoning[key]
            if (!o) return null
            return (
              <div className="lens-box" key={key}>
                <div className="lens-head">
                  <span>{MODULE_LABELS[key]}</span>
                  <span>
                    <span className={`pill ${stanceClass(o.stance)}`}>{prettyStance(o.stance)}</span>
                    {' '}
                    <span style={{ color: 'var(--faint)', fontSize: 11 }}>
                      conf {o.confidence?.score?.toFixed(0) ?? '—'}/{o.confidence?.band ?? '—'}
                    </span>
                  </span>
                </div>
                {o.stance_rationale && (
                  <div className="factor" style={{ color: 'var(--dim)' }}>{o.stance_rationale}</div>
                )}
                {(o.positive_factors || []).map((f, i) => (
                  <div className="factor pos" key={`p${i}`}>+ {f}</div>
                ))}
                {(o.negative_factors || []).map((f, i) => (
                  <div className="factor neg" key={`n${i}`}>− {f}</div>
                ))}
                {(o.knowledge_gaps || []).length > 0 && (
                  <div className="factor" style={{ color: 'var(--faint)', fontSize: 11 }}>
                    Data kurang: {o.knowledge_gaps.join(', ')}
                  </div>
                )}
                {(o.flag_responses || []).map((fr, i) => (
                  <div className="factor" key={`fr${i}`} style={{ color: 'var(--warn)', fontSize: 11 }}>
                    ⚑ {fr.flag_id} ({fr.impact}): {fr.rationale}
                  </div>
                ))}
              </div>
            )
          })}
        </div>
      )}

      {(risk?.flags?.length > 0 || risk?.red_flags?.length > 0) && (
        <div className="msection">
          <div className="msection-title">
            Risk / Red Flags{risk.risk_score != null ? ` (score ${risk.risk_score.toFixed(0)})` : ''}
          </div>
          {(risk.flags || []).map((f, i) => (
            <div className={`flag${f.severity === 'tinggi' ? ' medium' : ''}`} key={`f${i}`}>
              <strong>{f.flag_id}</strong> ({f.severity} · {f.status}) — {f.evidence_note}
            </div>
          ))}
          {(risk.red_flags || []).map((f, i) => (
            <div className={`flag${f.severity === 'medium' ? ' medium' : ''}`} key={`rf${i}`}>
              <strong>{f.flag_type}</strong> ({f.severity}) — {f.description}
            </div>
          ))}
        </div>
      )}

      {confidence && (
        <div className="msection">
          <div className="msection-title">
            Confidence Report — overall {confidence.overall?.score?.toFixed(0) ?? '—'}%{' '}
            <span className={`pill ${bandClass(confidence.overall?.band)}`}>{confidence.overall?.band || '—'}</span>
          </div>
          <div className="mrow">
            {Object.entries(confidence.by_section || {}).map(([name, sec]) => (
              <div className="mcell" key={name}>
                <div className="mcell-label">{prettyLabel(name)}</div>
                <div className="mcell-val">{sec.score.toFixed(0)}%</div>
              </div>
            ))}
          </div>
          {(confidence.overall?.limiters || []).length > 0 && (
            <p className="narrative" style={{ marginTop: 8 }}>
              <strong>Pembatas:</strong> {confidence.overall.limiters.join(' · ')}
            </p>
          )}
        </div>
      )}

      {catalyst && (catalyst.catalysts || []).length > 0 && (
        <div className="msection">
          <div className="msection-title">Katalis Mendatang</div>
          {catalyst.catalysts.map((c, i) => (
            <div className="lens-box" key={i}>
              <div className="lens-head">
                <span>{c.kind} · {c.expected_at}{c.expected_at_end ? `–${c.expected_at_end}` : ''}</span>
                <span className={`pill ${c.certainty === 'scheduled' ? 'ok' : c.certainty === 'expected' ? 'warn' : 'neutral'}`}>
                  {c.certainty}
                </span>
              </div>
              <div className="factor" style={{ color: 'var(--faint)', fontSize: 11 }}>
                berlaku sampai {c.expires_at}
              </div>
            </div>
          ))}
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

      {historical && (historical.entries || []).length > 0 && (
        <div className="msection">
          <div className="msection-title">
            Historical Tracking ({historical.total_entries || historical.entries.length} snapshot)
          </div>
          {historical.entries.slice().reverse().map((e, i) => {
            const ao = e.aggregator_output || {}
            const syn = ao.synthesis
            return (
              <div className="lens-box" key={i}>
                <div className="lens-head">
                  <span>{e.analyzed_at?.slice(0, 10) || '—'}</span>
                  <span>
                    {ao.halted ? (
                      <span className="pill bad">halted</span>
                    ) : syn?.full_convergence ? (
                      <span className="pill ok">konvergen</span>
                    ) : (
                      <span className="pill neutral">divergen</span>
                    )}
                  </span>
                </div>
                {syn?.narrative && (
                  <div className="factor" style={{ color: 'var(--dim)' }}>{syn.narrative}</div>
                )}
                <div className="factor" style={{ color: 'var(--faint)', fontSize: 11 }}>
                  {e.outcome != null ? 'outcome tercatat' : 'outcome: menunggu evaluasi v2.1'}
                </div>
              </div>
            )
          })}
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
