import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import { ratingClass } from '../format'

export default function ReasoningView({ onSelectTicker }) {
  const { data, error } = useStageData(api.reasoning)

  if (error) return <div className="empty">Gagal memuat data/reasoning_outputs.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const outs = data.reasoning_outputs || []
  const avgAgree = outs.reduce((s, o) => s + o.lens_agreement, 0) / (outs.length || 1)
  const highDiv = outs.filter((o) => o.divergence_level === 'high').length

  const stats = [
    { label: 'Total', value: outs.length },
    { label: 'Avg Lens Agreement', value: `${avgAgree.toFixed(0)}%` },
    { label: 'High Divergence', value: highDiv, tone: highDiv ? 'warn' : undefined },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    {
      key: 'quality',
      label: 'Quality',
      render: (r) => r.quality_output?.conviction_score?.toFixed(0) ?? '—',
      sortValue: (r) => r.quality_output?.conviction_score,
    },
    {
      key: 'speculative',
      label: 'Speculative',
      render: (r) => r.speculative_output?.conviction_score?.toFixed(0) ?? '—',
      sortValue: (r) => r.speculative_output?.conviction_score,
    },
    {
      key: 'multibagger',
      label: 'Multibagger',
      render: (r) => r.multibagger_output?.conviction_score?.toFixed(0) ?? '—',
      sortValue: (r) => r.multibagger_output?.conviction_score,
    },
    { key: 'final_score', label: 'Final Score', render: (r) => <strong>{r.final_score.toFixed(0)}</strong>, sortValue: (r) => r.final_score },
    {
      key: 'stance',
      label: 'Stance',
      render: (r) => <span className={`pill ${ratingClass(r.final_stance)}`}>{r.final_stance}</span>,
    },
    {
      key: 'divergence',
      label: 'Divergence',
      render: (r) => (
        <span className={`pill ${r.divergence_level === 'high' ? 'bad' : r.divergence_level === 'medium' ? 'warn' : 'ok'}`}>
          {r.divergence_level}
        </span>
      ),
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={outs} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
