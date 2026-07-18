import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import Bar from '../components/Bar'
import { fmtPct } from '../format'

export default function KnowledgeView({ onSelectTicker }) {
  const { data, error } = useStageData(api.knowledge)

  if (error) return <div className="empty">Gagal memuat data/knowledge.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const profiles = data.profiles || []
  const avgCompletion =
    profiles.reduce((s, p) => s + (p.metadata.fields_completed / p.metadata.fields_expected) * 100, 0) /
    (profiles.length || 1)

  const stats = [
    { label: 'Profiles', value: profiles.length },
    { label: 'Avg Completion', value: `${avgCompletion.toFixed(0)}%` },
  ]

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
      key: 'completion',
      label: 'Completion',
      render: (r) => <Bar pct={(r.metadata.fields_completed / r.metadata.fields_expected) * 100} />,
      sortValue: (r) => r.metadata.fields_completed / r.metadata.fields_expected,
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={profiles} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
