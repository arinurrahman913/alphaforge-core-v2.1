import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import Bar from '../components/Bar'

export default function RiskView({ onSelectTicker }) {
  const { data, error } = useStageData(api.risk)

  if (error) return <div className="empty">Gagal memuat data/risk_assessments.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const assessments = data.assessments || []
  const avg = assessments.reduce((s, a) => s + a.risk_score, 0) / (assessments.length || 1)
  const highRisk = assessments.filter((a) => a.risk_rating === 'high' || a.risk_rating === 'critical').length
  const totalFlags = assessments.reduce((s, a) => s + a.red_flags.length, 0)

  const stats = [
    { label: 'Assessed', value: assessments.length },
    { label: 'Avg Risk Score', value: avg.toFixed(0) },
    { label: 'High Risk', value: highRisk, tone: highRisk ? 'bad' : undefined },
    { label: 'Total Red Flags', value: totalFlags, tone: 'warn' },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    {
      key: 'risk_score',
      label: 'Risk Score',
      render: (r) => <Bar pct={r.risk_score} tone={r.risk_score > 60 ? 'bad' : r.risk_score > 30 ? 'warn' : 'good'} />,
      sortValue: (r) => r.risk_score,
    },
    { key: 'governance', label: 'Governance', render: (r) => r.governance_risk_score.toFixed(0), sortValue: (r) => r.governance_risk_score },
    { key: 'financial', label: 'Financial', render: (r) => r.financial_risk_score.toFixed(0), sortValue: (r) => r.financial_risk_score },
    { key: 'momentum', label: 'Momentum', render: (r) => r.momentum_risk_score.toFixed(0), sortValue: (r) => r.momentum_risk_score },
    { key: 'valuation', label: 'Valuation', render: (r) => r.valuation_risk_score.toFixed(0), sortValue: (r) => r.valuation_risk_score },
    { key: 'high_flags', label: 'High Flags', render: (r) => r.high_severity_count, sortValue: (r) => r.high_severity_count },
    {
      key: 'rating',
      label: 'Rating',
      render: (r) => (
        <span className={`pill ${r.risk_rating === 'low' ? 'ok' : r.risk_rating === 'medium' ? 'warn' : 'bad'}`}>
          {r.risk_rating}
        </span>
      ),
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={assessments} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
