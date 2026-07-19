import { api } from '../api'
import { useStageData } from '../useStageData'
import StatCards from '../components/StatCards'
import DataTable from '../components/DataTable'
import { fmtMoney, fmtNum } from '../format'

const TIER_ORDER = ['mega_cap', 'large_cap', 'mid_cap', 'small_cap', 'micro_cap']
const TIER_LABELS = {
  mega_cap: 'Mega Cap (>$100B)',
  large_cap: 'Large Cap ($10B-$100B)',
  mid_cap: 'Mid Cap ($2B-$10B)',
  small_cap: 'Small Cap ($300M-$2B)',
  micro_cap: 'Micro Cap (<$300M)',
}

// SCREENING_MARKET_CAP_TIERS_V2_BUILD_TEST_MARKER_XYZ123

export default function ScreeningView({ onSelectTicker }) {
  const { data, error } = useStageData(api.screening)

  if (error) return <div className="empty">Gagal memuat data/screening.json: {error}</div>
  if (!data) return <div className="loading">Memuat…</div>

  const passed = data.passed || []
  const excluded = data.hard_excluded || []

  const stats = [
    { label: 'Universe Raw', value: data.universe_raw?.toLocaleString() ?? '—' },
    { label: 'After Cheap Filter', value: data.universe_after_cheap_filter?.toLocaleString() ?? '—' },
    { label: 'Scanned', value: data.universe_scanned ?? '—' },
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
      key: 'flags',
      label: 'Flags',
      render: (r) => (
        <span style={{ whiteSpace: 'normal', maxWidth: 280, display: 'inline-block' }}>
          {(r.soft_flags || []).join(', ') || '—'}
        </span>
      ),
    },
  ]

  // Group passed tickers by market cap tier
  const tierGroups = {}
  TIER_ORDER.forEach(tier => {
    tierGroups[tier] = passed.filter(t => t.market_cap_tier === tier)
  })

  return (
    <>
      <StatCards stats={stats} />

      <div style={{ marginTop: '2rem' }}>
        {TIER_ORDER.map(tier => {
          const tickers = tierGroups[tier]
          if (tickers.length === 0) return null

          return (
            <div key={tier} style={{ marginBottom: '3rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem',
                marginBottom: '1rem',
                paddingBottom: '0.5rem',
                borderBottom: '1px solid var(--border)',
              }}>
                <h3 style={{ margin: 0, fontSize: '1.3rem' }}>{TIER_LABELS[tier]}</h3>
                <span style={{
                  backgroundColor: 'var(--success)',
                  color: 'white',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '1rem',
                  fontSize: '0.9rem',
                  fontWeight: 'bold',
                }}>
                  {tickers.length} tickers
                </span>
              </div>
              <DataTable
                columns={columns}
                rows={tickers}
                onRowClick={(r) => onSelectTicker(r.ticker)}
              />
            </div>
          )
        })}
      </div>

      {excluded.length > 0 && (
        <div style={{ marginTop: '3rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem',
            marginBottom: '1rem',
            paddingBottom: '0.5rem',
            borderBottom: '1px solid var(--border)',
          }}>
            <h3 style={{ margin: 0, fontSize: '1.3rem' }}>Hard Excluded</h3>
            <span style={{
              backgroundColor: 'var(--warning)',
              color: 'white',
              padding: '0.25rem 0.75rem',
              borderRadius: '1rem',
              fontSize: '0.9rem',
              fontWeight: 'bold',
            }}>
              {excluded.length} tickers
            </span>
          </div>
          <DataTable
            columns={[
              { key: 'ticker', label: 'Ticker', render: (r) => <span className="ticker">{r.ticker}</span> },
              { key: 'exchange', label: 'Exchange', render: (r) => r.exchange },
              { key: 'hard_exclude_reason', label: 'Reason', render: (r) => r.hard_exclude_reason || '—' },
              { key: 'last_price', label: 'Price', render: (r) => r.last_price ? `$${fmtNum(r.last_price, 2)}` : '—', sortValue: (r) => r.last_price },
            ]}
            rows={excluded}
            onRowClick={(r) => onSelectTicker(r.ticker)}
          />
        </div>
      )}
    </>
  )
}
