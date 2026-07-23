import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'

// HistoricalTimeline v2.0 (Data Contracts §8): menyimpan snapshot
// AggregatorOutput utuh per hari (HistoricalEntry). EVALUASI terhadap outcome
// nyata sengaja DITUNDA ke v2.1 (bentuk outcome belum diputuskan), jadi
// `outcome` selalu null untuk sekarang — view ini menampilkan penyimpanannya,
// bukan akurasi (yang belum bisa dihitung).
export default function HistoricalView({ onSelectTicker }) {
  const { data, error } = useStageData(api.historical)

  if (error) return <div className="empty">Gagal memuat data/historical_timeline.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const timelines = Object.values(data)
  const totalEntries = timelines.reduce((s, t) => s + (t.total_entries || 0), 0)
  const withOutcome = timelines.filter((t) =>
    (t.entries || []).some((e) => e.outcome != null),
  ).length

  const stats = [
    { label: 'Tickers Tracked', value: timelines.length },
    { label: 'Total Snapshots', value: totalEntries },
    { label: 'Dengan Outcome', value: withOutcome, tone: withOutcome ? 'good' : undefined },
  ]

  const lastEntry = (t) => (t.entries && t.entries.length ? t.entries[t.entries.length - 1] : null)

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    { key: 'total', label: 'Snapshots', render: (r) => r.total_entries || 0, sortValue: (r) => r.total_entries || 0 },
    {
      key: 'last_date',
      label: 'Snapshot Terakhir',
      render: (r) => (r.last_entry_date ? r.last_entry_date.slice(0, 10) : '—'),
      sortValue: (r) => r.last_entry_date,
    },
    {
      key: 'last_halted',
      label: 'Status Terakhir',
      render: (r) => {
        const e = lastEntry(r)
        const halted = e?.aggregator_output?.halted
        if (halted === true) return <span className="pill bad">halted</span>
        if (halted === false) return <span className="pill ok">analyzed</span>
        return '—'
      },
    },
    {
      key: 'outcome',
      label: 'Outcome',
      render: (r) => {
        const e = lastEntry(r)
        return e?.outcome != null ? 'ada' : <span style={{ color: 'var(--faint)' }}>menunggu v2.1</span>
      },
    },
  ]

  return (
    <>
      <StatCards stats={stats} />
      <p className="narrative" style={{ margin: '0 0 12px', color: 'var(--dim)', fontSize: 13 }}>
        Menyimpan snapshot analisa utuh sejak hari pertama (v2.0). Evaluasi akurasi terhadap pergerakan harga nyata
        menyusul di v2.1 — kolom Outcome masih kosong secara sengaja sampai bentuk pengukurannya diputuskan.
      </p>
      <DataTable columns={columns} rows={timelines} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
