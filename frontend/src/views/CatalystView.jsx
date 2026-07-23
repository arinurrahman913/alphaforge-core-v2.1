import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import HBarChart from '../components/HBarChart'

// CatalystSet (Data Contracts §5b): peristiwa mendatang per ticker (terutama
// earnings). certainty: scheduled (pasti) / expected (estimasi) / rumored
// (tidak dihasilkan sekarang — butuh parsing berita).
const certaintyClass = (c) => (c === 'scheduled' ? 'ok' : c === 'expected' ? 'warn' : 'neutral')

export default function CatalystView({ onSelectTicker }) {
  const { data, error } = useStageData(api.catalyst)

  if (error) return <div className="empty">Gagal memuat data/catalysts.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const sets = data.catalyst_sets || []
  const withUpcoming = sets.filter((s) => (s.catalysts || []).some((c) => c.certainty !== 'rumored')).length
  const missing = sets.filter((s) => s.status === 'missing').length

  const stats = [
    { label: 'Total', value: sets.length },
    { label: 'Ada Katalis Mendatang', value: withUpcoming, tone: 'good' },
    { label: 'Data Tidak Tersedia', value: missing, tone: missing ? 'warn' : undefined },
  ]

  // Katalis terdekat (tanggal paling awal) per ticker untuk kolom ringkas.
  const nearest = (s) => {
    const cs = s.catalysts || []
    if (!cs.length) return null
    return [...cs].sort((a, b) => a.expected_at.localeCompare(b.expected_at))[0]
  }

  const columns = [
    { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
    {
      key: 'count',
      label: 'Jumlah Katalis',
      render: (r) => (r.catalysts?.length || 0),
      sortValue: (r) => r.catalysts?.length || 0,
    },
    {
      key: 'next',
      label: 'Terdekat',
      render: (r) => {
        const c = nearest(r)
        return c ? `${c.kind} · ${c.expected_at}` : '—'
      },
      sortValue: (r) => nearest(r)?.expected_at || '9999',
    },
    {
      key: 'certainty',
      label: 'Kepastian',
      render: (r) => {
        const c = nearest(r)
        return c ? <span className={`pill ${certaintyClass(c.certainty)}`}>{c.certainty}</span> : '—'
      },
    },
    {
      key: 'status',
      label: 'Status',
      render: (r) => <span className={`pill ${r.status === 'ok' ? 'ok' : 'neutral'}`}>{r.status}</span>,
    },
  ]

  // Distribusi jenis katalis & kepastian.
  const kindCounts = {}
  const certCounts = {}
  sets.forEach((s) =>
    (s.catalysts || []).forEach((c) => {
      kindCounts[c.kind] = (kindCounts[c.kind] || 0) + 1
      certCounts[c.certainty] = (certCounts[c.certainty] || 0) + 1
    }),
  )
  const kindChart = Object.entries(kindCounts).map(([k, count]) => ({ label: k, count, color: 'var(--accent)' }))
  const certChart = [
    { label: 'Scheduled', count: certCounts.scheduled || 0, color: 'var(--good)' },
    { label: 'Expected', count: certCounts.expected || 0, color: 'var(--warn)' },
    { label: 'Rumored', count: certCounts.rumored || 0, color: 'var(--dim)' },
  ]

  // Default urut: yang punya katalis terdekat paling atas.
  const sorted = [...sets].sort((a, b) => (nearest(a)?.expected_at || '9999').localeCompare(nearest(b)?.expected_at || '9999'))

  return (
    <>
      <StatCards stats={stats} />
      <div className="chart-row">
        <HBarChart title="Jenis Katalis" data={kindChart.length ? kindChart : [{ label: '—', count: 0, color: 'var(--dim)' }]} />
        <HBarChart title="Tingkat Kepastian" data={certChart} />
      </div>
      <DataTable columns={columns} rows={sorted} onRowClick={(r) => onSelectTicker(r.ticker)} />
    </>
  )
}
