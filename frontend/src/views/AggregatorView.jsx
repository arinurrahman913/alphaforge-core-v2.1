import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import HBarChart from '../components/HBarChart'
import { bandClass } from '../format'

// AggregatorOutput (Data Contracts §7, D-04): TIDAK ada rekomendasi/skor/
// ranking tunggal — sengaja. Yang ditampilkan: 3 modul berdampingan (via
// Synthesis: agreements/divergences), confidence terendah, surprise
// (keunikan kombinasi stance vs populasi sesi), dan status halted.
export default function AggregatorView({ onSelectTicker }) {
  const { data, error } = useStageData(api.aggregator)

  if (error) return <div className="empty">Gagal memuat data/final_recommendations.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const outs = data.recommendations || []
  const halted = outs.filter((o) => o.halted).length
  const fullConv = outs.filter((o) => o.synthesis?.full_convergence).length
  const withDivergence = outs.filter((o) => (o.synthesis?.divergences?.length || 0) > 0).length

  const stats = [
    { label: 'Total', value: outs.length },
    { label: 'Konvergen penuh', value: fullConv, tone: 'good' },
    { label: 'Ada divergensi', value: withDivergence, tone: withDivergence ? 'warn' : undefined },
    { label: 'Halted (ekstrem)', value: halted, tone: halted ? 'bad' : undefined },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    {
      key: 'status',
      label: 'Status',
      render: (r) =>
        r.halted ? (
          <span className="pill bad" title={r.halt_reason || ''}>halted</span>
        ) : r.synthesis?.full_convergence ? (
          <span className="pill ok">konvergen</span>
        ) : (
          <span className="pill neutral">divergen</span>
        ),
    },
    {
      key: 'agreements',
      label: 'Kesepakatan',
      render: (r) => r.synthesis?.agreements?.length ?? '—',
      sortValue: (r) => r.synthesis?.agreements?.length ?? -1,
    },
    {
      key: 'divergences',
      label: 'Perbedaan',
      render: (r) => r.synthesis?.divergences?.length ?? '—',
      sortValue: (r) => r.synthesis?.divergences?.length ?? -1,
    },
    {
      key: 'confidence',
      label: 'Confidence',
      render: (r) => {
        const c = r.synthesis?.confidence
        return c ? <span className={`pill ${bandClass(c.band)}`}>{c.score.toFixed(0)} · {c.band}</span> : '—'
      },
      sortValue: (r) => r.synthesis?.confidence?.score,
    },
    {
      key: 'surprise',
      label: 'Surprise',
      render: (r) => (r.synthesis?.surprise != null ? r.synthesis.surprise.toFixed(2) : '—'),
      sortValue: (r) => r.synthesis?.surprise,
    },
    {
      key: 'flags',
      label: 'Risk Flags',
      render: (r) => {
        const triggered = (r.risk_flags || []).filter((f) => f.status === 'triggered').length
        return triggered > 0 ? <span className="pill warn">{triggered} triggered</span> : (r.risk_flags?.length ?? 0)
      },
      sortValue: (r) => (r.risk_flags || []).filter((f) => f.status === 'triggered').length,
    },
  ]

  // Surprise tertinggi = kombinasi stance paling tidak biasa di populasi sesi
  // ini — ini yang "menarik untuk dilihat", bukan skor rekomendasi.
  const sorted = [...outs].sort((a, b) => (b.synthesis?.surprise ?? -1) - (a.synthesis?.surprise ?? -1))

  const statusChart = [
    { label: 'Konvergen', count: fullConv, color: 'var(--good)' },
    { label: 'Divergen', count: withDivergence, color: 'var(--warn)' },
    { label: 'Halted', count: halted, color: 'var(--bad)' },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <div className="chart-row">
        <HBarChart title="Distribusi Status Sintesis" data={statusChart} />
      </div>
      <p className="narrative" style={{ margin: '0 0 12px', color: 'var(--dim)', fontSize: 13 }}>
        Diurutkan berdasarkan <strong>surprise</strong> — kombinasi stance paling tidak biasa di populasi sesi ini di atas.
        Tidak ada skor rekomendasi tunggal (Data Contracts D-04): buka satu ticker untuk melihat ketiga lensa + sintesisnya.
      </p>
      <DataTable columns={columns} rows={sorted} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
