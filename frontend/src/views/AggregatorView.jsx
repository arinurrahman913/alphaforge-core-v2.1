import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import Bar from '../components/Bar'
import { ratingClass } from '../format'

export default function AggregatorView({ onSelectTicker }) {
  const { data, error } = useStageData(api.aggregator)

  if (error) return <div className="empty">Gagal memuat data/final_recommendations.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const recs = data.recommendations || []
  const dist = {}
  recs.forEach((r) => (dist[r.recommendation] = (dist[r.recommendation] || 0) + 1))

  const stats = [
    { label: 'Total', value: recs.length },
    { label: 'Strong Buy', value: dist.strong_buy || 0, tone: 'good' },
    { label: 'Buy', value: dist.buy || 0, tone: 'good' },
    { label: 'Hold', value: dist.hold || 0 },
    { label: 'Sell / Strong Sell', value: (dist.sell || 0) + (dist.strong_sell || 0), tone: 'bad' },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    {
      key: 'recommendation',
      label: 'Recommendation',
      render: (r) => <span className={`pill ${ratingClass(r.recommendation)}`}>{r.recommendation.replace('_', ' ')}</span>,
    },
    { key: 'conviction', label: 'Conviction', render: (r) => <Bar pct={r.conviction} />, sortValue: (r) => r.conviction },
    { key: 'confidence', label: 'Confidence', render: (r) => r.confidence_score.toFixed(0), sortValue: (r) => r.confidence_score },
    { key: 'risk', label: 'Risk', render: (r) => r.risk_score.toFixed(0), sortValue: (r) => r.risk_score },
    { key: 'reasoning', label: 'Reasoning', render: (r) => r.reasoning_score.toFixed(0), sortValue: (r) => r.reasoning_score },
    { key: 'red_flags', label: 'Red Flags', render: (r) => r.red_flags.length, sortValue: (r) => r.red_flags.length },
  ]

  const sortedByConviction = [...recs].sort((a, b) => b.conviction - a.conviction)

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={sortedByConviction} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
