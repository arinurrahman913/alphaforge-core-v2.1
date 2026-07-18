import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import { fmtMoney, fmtNum, ratingClass } from '../format'

export default function EvidenceView({ onSelectTicker }) {
  const { data, error } = useStageData(api.evidence)

  if (error) return <div className="empty">Gagal memuat data/evidence.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const pkgs = data.packages || []
  const avgMcap = pkgs.reduce((s, p) => s + (p.price_market?.market_cap || 0), 0) / (pkgs.length || 1)
  const withSecQ = pkgs.filter((p) => p.fundamental?.quarterly_data?.length).length
  const withFilings = pkgs.filter((p) => p.sec_filings?.metadata?.status === 'ok').length

  const stats = [
    { label: 'Packages', value: pkgs.length },
    { label: 'Avg Market Cap', value: fmtMoney(avgMcap) },
    { label: 'SEC Quarterly OK', value: `${withSecQ}/${pkgs.length}`, tone: 'good' },
    { label: 'SEC Filings OK', value: `${withFilings}/${pkgs.length}`, tone: 'good' },
  ]

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    {
      key: 'price',
      label: 'Price',
      render: (r) => `$${fmtNum(r.price_market?.close, 2)}`,
      sortValue: (r) => r.price_market?.close,
    },
    {
      key: 'market_cap',
      label: 'Market Cap',
      render: (r) => fmtMoney(r.price_market?.market_cap),
      sortValue: (r) => r.price_market?.market_cap,
    },
    {
      key: 'revenue',
      label: 'Revenue',
      render: (r) => fmtMoney(r.fundamental?.revenue),
      sortValue: (r) => r.fundamental?.revenue,
    },
    {
      key: 'net_income',
      label: 'Net Income',
      render: (r) => fmtMoney(r.fundamental?.net_income),
      sortValue: (r) => r.fundamental?.net_income,
    },
    {
      key: 'pe_ratio',
      label: 'P/E',
      render: (r) => (r.fundamental?.pe_ratio ? `${r.fundamental.pe_ratio.toFixed(1)}x` : '—'),
      sortValue: (r) => r.fundamental?.pe_ratio,
    },
    {
      key: 'quarterly',
      label: 'SEC Qtrly',
      render: (r) => (
        <span className={`pill ${r.fundamental?.quarterly_data?.length ? 'ok' : 'neutral'}`}>
          {r.fundamental?.quarterly_data?.length || 0} qtrs
        </span>
      ),
      sortValue: (r) => r.fundamental?.quarterly_data?.length || 0,
    },
    {
      key: 'filings',
      label: 'SEC Filings',
      render: (r) => (
        <span className={`pill ${ratingClass(r.sec_filings?.metadata?.status)}`}>
          {r.sec_filings?.metadata?.status || '—'}
        </span>
      ),
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <DataTable columns={columns} rows={pkgs} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
