import { useEffect } from 'react'
import { ratingClass, prettyLabel } from '../format'

// Modal transparansi untuk stat tiles Layer 1: menjelaskan alasan + perhitungan
// tiap angka (Layer Score, Confidence, Komponen, OK, Degraded).
export default function StatDetailModal({ which, data, onClose }) {
  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!which || !data) return null

  const ls = data.layer_score
  const conf = data.context_summary?.confidence
  const comps = Object.entries(data.components || {})

  const TITLES = {
    score: `Layer Score — ${ls ? ls.final_score.toFixed(0) : '—'}${ls?.band_label ? ` · ${ls.band_label}` : ''}`,
    confidence: `Confidence — ${conf?.score != null ? conf.score.toFixed(0) : '—'}%`,
    components: `Komponen — ${comps.length}`,
    ok: `Komponen OK — ${comps.filter(([, c]) => c.status === 'ok').length}`,
    degraded: `Degraded — ${comps.filter(([, c]) => c.status !== 'ok').length}`,
  }

  return (
    <div className="modal" onClick={(e) => e.target.classList.contains('modal') && onClose()}>
      <div className="modal-box">
        <div className="modal-head">
          <h2>{TITLES[which]}</h2>
          <button className="x" onClick={onClose}>
            &times;
          </button>
        </div>
        <div className="modal-body">
          {which === 'score' && <ScoreDetail ls={ls} />}
          {which === 'confidence' && <ConfidenceDetail conf={conf} />}
          {(which === 'components' || which === 'ok' || which === 'degraded') && (
            <ComponentsDetail comps={comps} filter={which} />
          )}
        </div>
      </div>
    </div>
  )
}

function ScoreDetail({ ls }) {
  if (!ls) return <p className="narrative">Data Layer Score tidak tersedia.</p>
  const rows = [...ls.contributions].sort((a, b) => b.weighted - a.weighted)
  const totalWeighted = rows.reduce((s, c) => s + c.weighted, 0)
  const totalWeight = rows.reduce((s, c) => s + c.weight, 0)

  return (
    <>
      <div className="msection">
        <div className="msection-title">Cara Hitung</div>
        <p className="narrative">
          Layer Score = rata-rata tertimbang skor tiap komponen (skala 0–100). Tiap komponen punya bobot; skornya
          dikali bobot, dijumlahkan, lalu dibagi total bobot komponen yang aktif (berstatus ok).
        </p>
        <p className="narrative" style={{ fontFamily: 'var(--mono)', fontSize: 13, marginTop: 10, color: 'var(--gold-hi)' }}>
          Σ(skor × bobot) ÷ Σ bobot = {totalWeighted.toFixed(1)} ÷ {totalWeight.toFixed(2)} = {ls.final_score.toFixed(0)}
        </p>
        {ls.reasoning && (
          <p className="narrative" style={{ fontSize: 12.5, marginTop: 8, opacity: 0.85 }}>
            {ls.reasoning}
          </p>
        )}
      </div>

      <div className="msection">
        <div className="msection-title">Rincian Kontribusi ({rows.length} komponen)</div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Komponen</th>
                <th>Skor</th>
                <th>Bobot</th>
                <th>Kontribusi</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.component} style={{ cursor: 'default' }}>
                  <td className="ticker">{prettyLabel(c.component)}</td>
                  <td>{c.score.toFixed(0)}</td>
                  <td>{(c.weight * 100).toFixed(0)}%</td>
                  <td style={{ color: 'var(--gold-hi)', fontFamily: 'var(--mono)' }}>{c.weighted.toFixed(2)}</td>
                </tr>
              ))}
              <tr style={{ cursor: 'default', borderTop: '1px solid var(--rule-strong)' }}>
                <td style={{ fontWeight: 700 }}>TOTAL</td>
                <td></td>
                <td style={{ fontFamily: 'var(--mono)' }}>{(totalWeight * 100).toFixed(0)}%</td>
                <td style={{ color: 'var(--gold-hi)', fontFamily: 'var(--mono)', fontWeight: 700 }}>{totalWeighted.toFixed(2)}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {ls.excluded?.length > 0 && (
        <div className="msection">
          <div className="msection-title">Dikecualikan</div>
          {ls.excluded.map((e) => (
            <div className="flag medium" key={e}>
              {prettyLabel(e)} — status degraded/missing, tidak diikutkan agar tidak menurunkan skor secara keliru. Bobotnya
              dinormalisasi ulang ke komponen lain.
            </div>
          ))}
        </div>
      )}
    </>
  )
}

function ConfidenceDetail({ conf }) {
  if (!conf) return <p className="narrative">Data confidence tidak tersedia.</p>
  return (
    <>
      <div className="msection">
        <div className="msection-title">Cara Hitung</div>
        <p className="narrative">
          Confidence menilai seberapa bisa dipercaya paket data ini — dari proporsi komponen yang berstatus ok,
          kesegaran (freshness) data, dan ada/tidaknya konflik antar-sinyal. Bukan penilaian bullish/bearish.
        </p>
        <div className="mrow" style={{ marginTop: 14 }}>
          <div className="mcell">
            <div className="mcell-label">Skor</div>
            <div className="mcell-val">{conf.score?.toFixed(0)}%</div>
          </div>
          <div className="mcell">
            <div className="mcell-label">Band</div>
            <div className="mcell-val">
              <span className={`pill ${ratingClass(conf.band)}`}>{conf.band}</span>
            </div>
          </div>
        </div>
      </div>

      {conf.reasons?.length > 0 && (
        <div className="msection">
          <div className="msection-title">Faktor Penilaian</div>
          {conf.reasons.map((r, i) => (
            <div className="factor" key={i}>
              {r}
            </div>
          ))}
        </div>
      )}

      {conf.limiters?.length > 0 && (
        <div className="msection">
          <div className="msection-title">Penekan Confidence</div>
          {conf.limiters.map((l) => (
            <div className="flag medium" key={l}>
              {l}
            </div>
          ))}
        </div>
      )}
    </>
  )
}

function ComponentsDetail({ comps, filter }) {
  let rows = comps
  if (filter === 'ok') rows = comps.filter(([, c]) => c.status === 'ok')
  if (filter === 'degraded') rows = comps.filter(([, c]) => c.status !== 'ok')

  return (
    <div className="msection">
      <div className="msection-title">
        {filter === 'degraded' ? 'Komponen degraded/missing' : filter === 'ok' ? 'Komponen berstatus ok' : 'Semua komponen'}
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Komponen</th>
              <th>Status</th>
              <th>Skor</th>
              <th>Kontribusi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(([key, c]) => (
              <tr key={key} style={{ cursor: 'default' }}>
                <td className="ticker">{prettyLabel(c.name || key)}</td>
                <td>
                  <span className={`pill ${ratingClass(c.status)}`}>{c.status}</span>
                </td>
                <td>{c.raw_score != null ? c.raw_score.toFixed(0) : '—'}</td>
                <td style={{ fontFamily: 'var(--mono)' }}>{c.contribution ? c.contribution.weighted.toFixed(2) : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {filter === 'degraded' &&
        rows.map(([key, c]) => (
          <p className="narrative" key={`n-${key}`} style={{ fontSize: 12.5, marginTop: 10, opacity: 0.85 }}>
            <b>{prettyLabel(c.name || key)}:</b> {c.note || c.narrative || 'Tidak ada catatan.'}
          </p>
        ))}
    </div>
  )
}
