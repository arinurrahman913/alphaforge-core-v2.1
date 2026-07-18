import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import { fmtPct, ratingClass } from '../format'

export default function HistoricalView({ onSelectTicker }) {
  const { data, error } = useStageData(api.historical)

  if (error) return <div className="empty">Gagal memuat data/historical_timeline.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const timelines = Object.values(data)
  const withOutcome = timelines.filter((t) => t.total_outcomes > 0)
  const totalCorrect = withOutcome.reduce((s, t) => s + t.correct_predictions, 0)
  const totalOutcomes = withOutcome.reduce((s, t) => s + t.total_outcomes, 0)
  const overallAcc = totalOutcomes ? (totalCorrect / totalOutcomes) * 100 : null

  const stats = [
    { label: 'Tickers Tracked', value: timelines.length },
    { label: 'With Outcome', value: withOutcome.length },
    {
      label: 'Overall Accuracy',
      value: overallAcc !== null ? `${overallAcc.toFixed(1)}%` : '—',
      tone: overallAcc !== null ? (overallAcc >= 50 ? 'good' : 'bad') : undefined,
    },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    { key: 'total_recs', label: 'Total Recs', render: (r) => r.total_recommendations, sortValue: (r) => r.total_recommendations },
    {
      key: 'last_rec',
      label: 'Last Recommendation',
      render: (r) => {
        const last = r.records[r.records.length - 1]
        return <span className={`pill ${ratingClass(last?.recommendation)}`}>{last?.recommendation || '—'}</span>
      },
    },
    {
      key: 'actual_return',
      label: 'Actual Return',
      render: (r) => {
        const last = r.records[r.records.length - 1]
        return last?.actual_return_pct !== undefined && last?.actual_return_pct !== null ? fmtPct(last.actual_return_pct) : 'pending'
      },
      sortValue: (r) => r.records[r.records.length - 1]?.actual_return_pct,
    },
    {
      key: 'outcome',
      label: 'Outcome',
      render: (r) => {
        const last = r.records[r.records.length - 1]
        if (last?.decision_correct === true) return <span className="pill ok">correct</span>
        if (last?.decision_correct === false) return <span className="pill bad">wrong</span>
        return '—'
      },
    },
    {
      key: 'accuracy',
      label: 'Accuracy',
      render: (r) => (r.accuracy_pct !== null && r.accuracy_pct !== undefined ? `${r.accuracy_pct.toFixed(0)}%` : '—'),
      sortValue: (r) => r.accuracy_pct,
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={timelines} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
