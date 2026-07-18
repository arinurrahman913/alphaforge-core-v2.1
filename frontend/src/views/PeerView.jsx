import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'

function pctileText(comp) {
  return comp?.percentile !== null && comp?.percentile !== undefined ? `${comp.percentile.toFixed(0)}th` : '—'
}

export default function PeerView({ onSelectTicker }) {
  const { data, error } = useStageData(api.peer)

  if (error) return <div className="empty">Gagal memuat data/peer_results.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const comps = data.comparisons || []
  const avgGroup = comps.reduce((s, c) => s + (c.peer_group?.group_size || 0), 0) / (comps.length || 1)

  const stats = [
    { label: 'Comparisons', value: comps.length },
    { label: 'Avg Group Size', value: avgGroup.toFixed(0) },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    { key: 'group_size', label: 'Group Size', render: (r) => r.peer_group?.group_size ?? '—', sortValue: (r) => r.peer_group?.group_size },
    {
      key: 'pe',
      label: 'P/E %ile',
      render: (r) => pctileText(r.pe_ratio_comparison),
      sortValue: (r) => r.pe_ratio_comparison?.percentile,
    },
    {
      key: 'pb',
      label: 'P/B %ile',
      render: (r) => pctileText(r.pb_ratio_comparison),
      sortValue: (r) => r.pb_ratio_comparison?.percentile,
    },
    {
      key: 'fcf',
      label: 'FCF Yield %ile',
      render: (r) => pctileText(r.fcf_yield_comparison),
      sortValue: (r) => r.fcf_yield_comparison?.percentile,
    },
    { key: 'basis', label: 'Basis', render: (r) => r.peer_group_basis || '—' },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={comps} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
