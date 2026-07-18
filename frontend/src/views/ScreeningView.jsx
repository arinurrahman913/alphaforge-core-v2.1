import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import { fmtMoney, fmtNum } from '../format'

export default function ScreeningView({ onSelectTicker }) {
  const { data, error } = useStageData(api.screening)

  if (error) return <div className="empty">Gagal memuat data/screening.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const passed = data.passed || []
  const excluded = data.hard_excluded || []
  const rows = [
    ...passed.map((t) => ({ ...t, _status: 'passed' })),
    ...excluded.map((t) => ({ ...t, _status: 'excluded' })),
  ]

  const stats = [
    { label: 'Universe Raw', value: data.universe_raw?.toLocaleString() ?? '—' },
    { label: 'After Cheap Filter', value: data.universe_after_cheap_filter?.toLocaleString() ?? '—' },
    { label: 'Discanned', value: data.universe_scanned ?? '—' },
    { label: 'Passed', value: passed.length, tone: 'good' },
    { label: 'Excluded', value: excluded.length, tone: 'bad' },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    { key: 'exchange', label: 'Exchange', render: (r) => r.exchange },
    { key: 'market_cap', label: 'Market Cap', render: (r) => fmtMoney(r.market_cap), sortValue: (r) => r.market_cap },
    {
      key: 'avg_dollar_volume_20d',
      label: 'Avg $Vol 20d',
      render: (r) => fmtMoney(r.avg_dollar_volume_20d),
      sortValue: (r) => r.avg_dollar_volume_20d,
    },
    { key: 'last_price', label: 'Price', render: (r) => `$${fmtNum(r.last_price, 2)}`, sortValue: (r) => r.last_price },
    {
      key: '_status',
      label: 'Status',
      render: (r) => <span className={`pill ${r._status === 'passed' ? 'ok' : 'bad'}`}>{r._status}</span>,
    },
    {
      key: 'flags',
      label: 'Flags / Reason',
      render: (r) => (
        <span style={{ whiteSpace: 'normal', maxWidth: 280, display: 'inline-block' }}>
          {r._status === 'passed' ? (r.soft_flags || []).join(', ') : r.hard_exclude_reason || '—'}
        </span>
      ),
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={rows} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
