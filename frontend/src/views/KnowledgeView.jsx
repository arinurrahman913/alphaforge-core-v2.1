import { useState } from 'react'
import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import Bar from '../components/Bar'
import Sparkline from '../components/Sparkline'
import Icon from '../components/Icon'
import { fmtPct } from '../format'

// Warna & ikon per sektor — sekadar variasi visual antar-card, tidak
// membawa arti finansial (beda dengan warna good/bad di tempat lain).
// Nama sektor mengikuti taksonomi Yahoo Finance (dari evidence.fundamental.sector
// mentah, bukan GICS baku) — mis. "Financial Services", "Consumer Cyclical",
// "Consumer Defensive", "Basic Materials" — bukan nama GICS yang mirip tapi beda.
const SECTOR_META = {
  'Technology': { color: '#818CF8', icon: 'activity' },
  'Healthcare': { color: '#4ADE80', icon: 'shield' },
  'Financial Services': { color: '#e8b84b', icon: 'dollar' },
  'Energy': { color: '#FBBF7A', icon: 'flame' },
  'Basic Materials': { color: '#22D3EE', icon: 'layers' },
  'Industrials': { color: '#94A3B8', icon: 'bars' },
  'Consumer Cyclical': { color: '#F472B6', icon: 'mood' },
  'Consumer Defensive': { color: '#4fd1e0', icon: 'droplet' },
  'Real Estate': { color: '#C4B5FD', icon: 'layers' },
  'Utilities': { color: '#60A5FA', icon: 'wave' },
  'Communication Services': { color: '#FB7185', icon: 'flow' },
  'Lainnya': { color: '#7c8595', icon: 'dot' },
}

function sectorMeta(sector) {
  return SECTOR_META[sector] || SECTOR_META['Lainnya']
}

function completion(p) {
  return (p.metadata.fields_completed / p.metadata.fields_expected) * 100
}

function groupBySector(profiles) {
  const groups = {}
  for (const p of profiles) {
    const key = p.sector || 'Lainnya'
    if (!groups[key]) groups[key] = []
    groups[key].push(p)
  }
  // Sektor dengan lebih banyak ticker ditampilkan lebih dulu.
  return Object.entries(groups).sort((a, b) => b[1].length - a[1].length)
}

const columns = [
  { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
  { key: 'size_category', label: 'Size', render: (r) => r.size_category || '—' },
  {
    key: 'return_1y',
    label: 'Return 1Y',
    render: (r) => fmtPct(r.historical_trend?.return_1y),
    sortValue: (r) => r.historical_trend?.return_1y,
  },
  {
    key: 'revenue_yoy',
    label: 'Rev YoY (Q terkini)',
    render: (r) => fmtPct(r.financial_health?.revenue_trend?.yoy_q4),
    sortValue: (r) => r.financial_health?.revenue_trend?.yoy_q4,
  },
  {
    key: 'gross_margin',
    label: 'Gross Margin',
    render: (r) => {
      const v = r.financial_health?.gross_margin_trend?.q4
      return v !== null && v !== undefined ? `${v.toFixed(1)}%` : '—'
    },
    sortValue: (r) => r.financial_health?.gross_margin_trend?.q4,
  },
  {
    key: 'pe_ratio',
    label: 'P/E',
    render: (r) => (r.valuation?.pe_ratio_trailing ? `${r.valuation.pe_ratio_trailing.toFixed(1)}x` : '—'),
    sortValue: (r) => r.valuation?.pe_ratio_trailing,
  },
  {
    key: 'insider',
    label: 'Insider (30d)',
    render: (r) => {
      const n = r.ownership?.insider_filing_activity_30d || 0
      return n > 0 ? <span className="pill ok" style={{ fontSize: 10 }}>{n} filing</span> : '—'
    },
    sortValue: (r) => r.ownership?.insider_filing_activity_30d || 0,
  },
  {
    key: 'completion',
    label: 'Completion',
    render: (r) => <Bar pct={completion(r)} />,
    sortValue: (r) => completion(r),
  },
]

export default function KnowledgeView({ onSelectTicker }) {
  const { data, error } = useStageData(api.knowledge)
  const [selectedSector, setSelectedSector] = useState(null)

  if (error) return <div className="empty">Gagal memuat data/knowledge.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const profiles = data.profiles || []
  const avgCompletion = profiles.reduce((s, p) => s + completion(p), 0) / (profiles.length || 1)
  const sectorGroups = groupBySector(profiles)

  if (selectedSector) {
    const sectorProfiles = sectorGroups.find(([s]) => s === selectedSector)?.[1] || []
    const meta = sectorMeta(selectedSector)
    return (
      <>
        <button className="btn-back" onClick={() => setSelectedSector(null)} style={{ marginBottom: 14 }}>
          ← Kembali ke semua sektor
        </button>
        <div className="msection-title" style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <span className="l1a-ic" style={{ '--c': meta.color, width: 30, height: 30 }}>
            <Icon name={meta.icon} size={15} />
          </span>
          {selectedSector} — {sectorProfiles.length} tickers
        </div>
        <DataTable columns={columns} rows={sectorProfiles} onRowClick={(r) => onSelectTicker(r.ticker)} />
      </>
    )
  }

  const stats = [
    { label: 'Profiles', value: profiles.length },
    { label: 'Sektor', value: sectorGroups.length },
    { label: 'Avg Completion', value: `${avgCompletion.toFixed(0)}%` },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <div className="l1a-grid">
        {sectorGroups.map(([sector, list], idx) => (
          <SectorCard
            key={sector}
            sector={sector}
            profiles={list}
            idx={idx}
            onClick={() => setSelectedSector(sector)}
          />
        ))}
      </div>
    </>
  )
}

function SectorCard({ sector, profiles, idx, onClick }) {
  const meta = sectorMeta(sector)
  const count = profiles.length

  const withReturn = profiles.filter((p) => p.historical_trend?.return_1y != null)
  const leader = withReturn.length
    ? withReturn.reduce((best, p) =>
        p.historical_trend.return_1y > best.historical_trend.return_1y ? p : best
      )
    : null

  const avgCompletion = profiles.reduce((s, p) => s + completion(p), 0) / (count || 1)
  const avgReturn1y = withReturn.length
    ? withReturn.reduce((s, p) => s + p.historical_trend.return_1y, 0) / withReturn.length
    : null

  const insiderActive = profiles.filter((p) => (p.ownership?.insider_filing_activity_30d || 0) > 0).length

  const trend = avgReturn1y == null ? 'flat' : avgReturn1y > 5 ? 'up' : avgReturn1y < -5 ? 'down' : 'flat'

  return (
    <div className="l1a-card" onClick={onClick} style={{ '--c': meta.color, '--i': idx }}>
      <div className="l1a-top">
        <div className="l1a-idwrap">
          <span className="l1a-ic">
            <Icon name={meta.icon} size={18} />
          </span>
          <div>
            <p className="l1a-label">{sector}</p>
            <div className="l1a-val">
              {count}
              <span className="u">tickers</span>
            </div>
          </div>
        </div>
        <span className="l1a-pill ok">{avgCompletion.toFixed(0)}%</span>
      </div>

      {leader && (
        <div className="l1a-mini">
          <div>
            <p className="l1a-mini-l">🏆 Pemimpin</p>
            <p className="l1a-mini-v">
              {leader.ticker} {fmtPct(leader.historical_trend?.return_1y)}
            </p>
          </div>
          <div>
            <p className="l1a-mini-l">P/E</p>
            <p className="l1a-mini-v">
              {leader.valuation?.pe_ratio_trailing ? `${leader.valuation.pe_ratio_trailing.toFixed(1)}x` : '—'}
            </p>
          </div>
          {insiderActive > 0 && (
            <div>
              <p className="l1a-mini-l">Insider Aktif</p>
              <p className="l1a-mini-v">{insiderActive}</p>
            </div>
          )}
        </div>
      )}

      <div className="l1a-chart">
        <Sparkline trend={trend} color={meta.color} seed={sector} height={36} />
      </div>

      <p className="l1a-foot">
        Rata-rata return 1Y: {avgReturn1y != null ? fmtPct(avgReturn1y) : '—'} · klik untuk lihat semua {count} ticker
      </p>
    </div>
  )
}
