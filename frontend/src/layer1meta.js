// Extractor per-komponen Layer 1 → { hero, unit, delta, stats, trend, inputsUsed }.
// Dipakai Layer1View untuk merender card ala Aurum. Detail lengkap tetap di modal.

const cap = (s) => (s ? String(s).charAt(0).toUpperCase() + String(s).slice(1) : s)
const sgn = (v, d = 1) => (v == null ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(d)}`)

// dir: 'up' | 'down' | 'flat'
export function describeComponent(key, c) {
  const v = c.value || {}
  const degraded = c.status !== 'ok'
  const accent = degraded ? 'cyan' : 'gold'

  switch (key) {
    case 'yield_curve':
      return {
        hero: sgn(v.spread_10y_2y, 2),
        unit: 'pp',
        delta: { text: cap(v.shape), dir: v.spread_10y_2y >= 0.25 ? 'up' : v.spread_10y_2y < 0 ? 'down' : 'flat' },
        trend: v.spread_10y_2y < 0 ? 'down' : 'up',
        accent,
      }

    case 'business_cycle_stage':
      return {
        hero: cap(v.stage),
        unit: null,
        delta: { text: v.unemployment_rising ? 'Pengangguran naik' : 'Momentum stabil', dir: v.unemployment_rising ? 'down' : 'up' },
        stats: [
          { l: 'GDP QoQ', v: `${sgn(v.gdp_qoq_pct)}%` },
          { l: 'Ind. Prod', v: `${sgn(v.indpro_yoy_pct)}%` },
          { l: 'Unemp.', v: `${v.unemployment_rate?.toFixed(1)}%` },
        ],
        trend: 'up',
        accent,
      }

    case 'market_regime':
      return {
        hero: Math.round(v.price).toLocaleString(),
        unit: 'SPX',
        delta: { text: cap(v.regime), dir: v.regime === 'bull' ? 'up' : v.regime === 'bear' ? 'down' : 'flat' },
        stats: [
          { l: 'ke MA200', v: `${sgn(v.distance_to_ma200_pct)}%` },
          { l: 'MA50', v: Math.round(v.ma50).toLocaleString() },
        ],
        trend: v.regime === 'bull' ? 'up' : v.regime === 'bear' ? 'down' : 'flat',
        accent,
      }

    case 'volatility_index':
      return {
        hero: v.vix?.toFixed(1),
        unit: 'VIX',
        delta: { text: v.vix < v.avg_5y ? 'Di bawah avg 5th' : 'Di atas avg 5th', dir: v.vix < v.avg_5y ? 'down' : 'up' },
        stats: [
          { l: 'Avg 5Y', v: v.avg_5y?.toFixed(1) },
          { l: 'Level', v: cap(v.level) },
        ],
        trend: v.vix < v.avg_5y ? 'down' : 'up',
        accent,
      }

    case 'liquidity_conditions':
      return {
        hero: `${sgn(v.m2_yoy_pct)}%`,
        unit: 'M2 YoY',
        delta: { text: v.tightening ? 'Tightening' : 'Easing', dir: v.tightening ? 'down' : 'up' },
        stats: [
          { l: 'Fed B/S Δ', v: `${v.fed_balance_sheet_change >= 0 ? '+' : ''}${Math.round(v.fed_balance_sheet_change / 1000)}B` },
          { l: 'Tightening', v: v.tightening ? 'Ya' : 'Tidak' },
        ],
        trend: v.tightening ? 'down' : 'up',
        accent,
      }

    case 'market_breadth':
      return {
        hero: `${v.pct_above_ma200?.toFixed(1)}%`,
        unit: '>MA200',
        delta: { text: v.advances > v.declines ? 'Advancing' : 'Declining', dir: v.advances > v.declines ? 'up' : 'down' },
        stats: [
          { l: 'Naik', v: String(v.advances) },
          { l: 'Turun', v: String(v.declines) },
          { l: 'Universe', v: String(v.universe_size) },
        ],
        trend: v.pct_above_ma200 >= 50 ? 'up' : 'down',
        accent,
      }

    case 'sector_rotation': {
      const lead = v.sectors?.[v.leader]?.relative_1m_pct
      const lag = v.sectors?.[v.laggard]?.relative_1m_pct
      return {
        hero: v.leader,
        unit: 'leads',
        delta: { text: lead != null ? `${sgn(lead)}pp vs SPY` : '—', dir: 'up' },
        stats: [
          { l: 'Leader', v: `${v.leader} ${lead != null ? sgn(lead) : ''}` },
          { l: 'Laggard', v: `${v.laggard} ${lag != null ? sgn(lag) : ''}` },
        ],
        trend: 'flat',
        accent,
      }
    }

    case 'money_flow': {
      const inflows = v.inflows || []
      const outflows = v.outflows || []
      const inN = inflows.length
      const outN = outflows.length
      return {
        hero: inN > outN ? String(inN) : outN > 0 ? String(outN) : '0',
        unit: inN > outN ? 'inflow' : outN > 0 ? 'outflow' : 'flat',
        delta: { text: outN > inN ? 'Net outflow' : inN > outN ? 'Net inflow' : 'Seimbang', dir: outN > inN ? 'down' : inN > outN ? 'up' : 'flat' },
        stats: [
          { l: 'Inflow', v: inflows.join(', ') || 'tidak ada' },
          { l: 'Outflow', v: outflows.join(', ') || 'tidak ada' },
        ],
        trend: outN > inN ? 'down' : inN > outN ? 'up' : 'flat',
        accent,
      }
    }

    case 'currency_dxy':
      return {
        hero: v.dxy?.toFixed(2),
        unit: 'DXY',
        delta: { text: `${sgn(v.change_30d_pct)}% 30h`, dir: v.change_30d_pct >= 0 ? 'up' : 'down' },
        trend: v.change_30d_pct >= 0 ? 'up' : 'down',
        accent,
      }

    case 'commodity_signals': {
      const avg = (v.gold_change_30d_pct + v.wti_change_30d_pct) / 2
      return {
        hero: `${sgn(avg, 0)}%`,
        unit: '30h avg',
        delta: { text: avg >= 0 ? 'Menguat' : 'Melemah', dir: avg >= 0 ? 'up' : 'down' },
        stats: [
          { l: 'Emas', v: `${sgn(v.gold_change_30d_pct)}%` },
          { l: 'WTI', v: `${sgn(v.wti_change_30d_pct)}%` },
        ],
        trend: avg >= 0 ? 'up' : 'down',
        accent,
      }
    }

    case 'macro_calendar': {
      const ev = (v.events || [])[0]
      const days = ev ? Math.max(0, Math.round((new Date(ev.date) - new Date()) / 86400000)) : null
      return {
        hero: days != null ? String(days) : '—',
        unit: 'hari',
        delta: ev ? { text: ev.label, dir: 'flat' } : null,
        stats: [
          { l: 'Berikutnya', v: ev ? ev.label : '—' },
          { l: 'Peristiwa', v: String((v.events || []).length) },
        ],
        trend: 'flat',
        accent,
      }
    }

    case 'market_sentiment':
      return {
        hero: Math.round(v.score_0_100).toString(),
        unit: '/100',
        delta: { text: cap(v.label), dir: 'flat' },
        stats: [
          { l: 'Signal', v: cap(v.label) },
          { l: 'Input', v: `${(v.inputs_used || []).length}/4` },
        ],
        inputsUsed: (v.inputs_used || []).length,
        trend: 'flat',
        accent,
      }

    default:
      return {
        hero: c.raw_score != null ? c.raw_score.toFixed(0) : '—',
        unit: null,
        delta: null,
        trend: c.raw_score >= 60 ? 'up' : c.raw_score <= 40 ? 'down' : 'flat',
        accent,
      }
  }
}

export function deltaArrow(dir) {
  return dir === 'up' ? '▲' : dir === 'down' ? '▼' : '◆'
}

const COMPONENT_ICON = {
  business_cycle_stage: 'cycle',
  sector_rotation: 'rotate',
  money_flow: 'flow',
  liquidity_conditions: 'droplet',
  yield_curve: 'chartline',
  market_regime: 'activity',
  macro_calendar: 'calendar',
  currency_dxy: 'dollar',
  commodity_signals: 'flame',
  volatility_index: 'wave',
  market_breadth: 'bars',
  market_sentiment: 'mood',
}

export function componentIcon(key) {
  return COMPONENT_ICON[key] || 'dot'
}
