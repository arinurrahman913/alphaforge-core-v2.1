import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import Bar from '../components/Bar'
import { ratingClass } from '../format'

export default function ConfidenceView({ onSelectTicker }) {
  const { data, error } = useStageData(api.confidence)

  if (error) return <div className="empty">Gagal memuat data/confidence_scores.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const scores = data.scores || []
  const avg = scores.reduce((s, x) => s + x.overall_confidence, 0) / (scores.length || 1)
  const highCount = scores.filter((s) => s.confidence_rating === 'high').length

  const stats = [
    { label: 'Total', value: scores.length },
    { label: 'Avg Confidence', value: `${avg.toFixed(0)}%` },
    { label: 'High Rating', value: highCount, tone: 'good' },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    { key: 'overall', label: 'Overall', render: (r) => <Bar pct={r.overall_confidence} />, sortValue: (r) => r.overall_confidence },
    { key: 'price', label: 'Price', render: (r) => `${r.price_data_confidence.toFixed(0)}%`, sortValue: (r) => r.price_data_confidence },
    {
      key: 'fundamentals',
      label: 'Fundamentals',
      render: (r) => `${r.fundamental_data_confidence.toFixed(0)}%`,
      sortValue: (r) => r.fundamental_data_confidence,
    },
    {
      key: 'ownership',
      label: 'Ownership',
      render: (r) => `${r.ownership_data_confidence.toFixed(0)}%`,
      sortValue: (r) => r.ownership_data_confidence,
    },
    {
      key: 'governance',
      label: 'Governance',
      render: (r) => `${r.governance_data_confidence.toFixed(0)}%`,
      sortValue: (r) => r.governance_data_confidence,
    },
    {
      key: 'rating',
      label: 'Rating',
      render: (r) => <span className={`pill ${ratingClass(r.confidence_rating)}`}>{r.confidence_rating}</span>,
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={scores} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
