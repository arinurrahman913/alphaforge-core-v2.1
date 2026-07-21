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
        delta: { text: v.vix < v.median_5y ? 'Di bawah median 5th' : 'Di atas median 5th', dir: v.vix < v.median_5y ? 'down' : 'up' },
        stats: [
          { l: 'Median 5Y', v: v.median_5y?.toFixed(1) },
          { l: 'Level', v: cap(v.level) },
        ],
        trend: v.vix < v.median_5y ? 'down' : 'up',
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
        delta: { text: v.interpretation || (v.advances > v.declines ? 'Advancing' : 'Declining'), dir: v.pct_above_ma200 >= 60 ? 'up' : v.pct_above_ma200 < 40 ? 'down' : 'flat' },
        stats: [
          { l: 'Naik', v: String(v.advances) },
          { l: 'Turun', v: String(v.declines) },
          { l: 'Universe', v: String(v.universe_size) },
        ],
        trend: v.pct_above_ma200 >= 50 ? 'up' : 'down',
        accent,
      }

    case 'sector_rotation': {
      const leaders = v.leaders || []
      const laggards = v.laggards || []
      const lead = leaders[0]?.relative_1m_pct
      return {
        hero: v.leader,
        unit: 'leads',
        delta: { text: lead != null ? `${sgn(lead)}pp vs SPY` : '—', dir: 'up' },
        stats: [
          { l: 'Top 3 Leader', v: leaders.map((l) => l.etf).join(', ') || v.leader },
          { l: 'Top 3 Laggard', v: laggards.map((l) => l.etf).join(', ') || v.laggard },
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
        delta: { text: `${sgn(v.change_30d_pct)}% 1bln`, dir: v.change_30d_pct >= 0 ? 'up' : 'down' },
        stats: [
          { l: 'Δ 1 bulan', v: `${sgn(v.change_30d_pct)}%` },
          { l: 'Δ 3 bulan', v: v.change_90d_pct != null ? `${sgn(v.change_90d_pct)}%` : '—' },
          { l: 'Level', v: cap(v.level) },
        ],
        trend: v.change_30d_pct >= 0 ? 'up' : 'down',
        accent,
      }

    case 'commodity_signals': {
      const reflationary = v.pattern === 'reflation' || v.pattern === 'inflation_shock'
      return {
        hero: v.pattern_label || '—',
        unit: null,
        delta: { text: `Oil ${sgn(v.wti_change_30d_pct, 0)}% · Cu ${sgn(v.copper_change_30d_pct, 0)}% · Au ${sgn(v.gold_change_30d_pct, 0)}%`, dir: 'flat' },
        stats: [
          { l: 'Oil (WTI)', v: `${sgn(v.wti_change_30d_pct)}%` },
          { l: 'Copper', v: `${sgn(v.copper_change_30d_pct)}%` },
          { l: 'Gold', v: `${sgn(v.gold_change_30d_pct)}%` },
        ],
        trend: reflationary ? 'up' : v.pattern === 'risk_off' || v.pattern === 'deflation' ? 'down' : 'flat',
        accent,
      }
    }

    case 'credit_spread': {
      const mom = v.momentum_30d_bps
      const warn = v.rising_fast && v.level === 'tight'
      return {
        hero: v.oas_bps != null ? String(Math.round(v.oas_bps)) : v.oas_pct?.toFixed(2),
        unit: 'bps OAS',
        delta: { text: warn ? `⚠ ${sgn(mom, 0)} bps/30h` : `${cap(v.level)} · ${sgn(mom, 0)} bps/30h`, dir: mom > 5 ? 'down' : mom < -5 ? 'up' : 'flat' },
        stats: [
          { l: 'Persentil 5Y', v: `${Math.round((v.percentile_5y ?? 0) * 100)}%` },
          { l: 'Momentum 30h', v: `${sgn(mom, 0)} bps` },
          { l: 'Level', v: cap(v.level) },
        ],
        trend: v.level === 'wide' || warn ? 'down' : v.level === 'tight' ? 'up' : 'flat',
        accent,
      }
    }

    case 'macro_calendar': {
      const top = (v.top_events || [])[0]
      const risk = v.event_risk || '—'
      return {
        hero: top ? String(top.days_until) : '—',
        unit: top ? 'hari' : null,
        delta: { text: risk, dir: risk.startsWith('High') ? 'down' : risk.startsWith('Medium') ? 'flat' : 'up' },
        stats: [
          { l: 'Berikutnya', v: top ? `${top.label} (${top.impact})` : '—' },
          { l: 'Peristiwa', v: String((v.events || []).length) },
        ],
        trend: risk.startsWith('High') ? 'down' : 'flat',
        accent,
      }
    }

    case 'market_sentiment': {
      const comp = v.composition
      return {
        hero: Math.round(v.score_0_100).toString(),
        unit: '/100',
        delta: { text: cap(v.label), dir: 'flat' },
        stats: comp
          ? [
              { l: 'Bullish', v: String(comp.bullish) },
              { l: 'Neutral', v: String(comp.neutral) },
              { l: 'Bearish', v: String(comp.bearish) },
            ]
          : [
              { l: 'Signal', v: cap(v.label) },
              { l: 'Input', v: `${(v.inputs_used || []).length}/${v.inputs_total || 6}` },
            ],
        inputsUsed: (v.inputs_used || []).length,
        inputsTotal: v.inputs_total || 6,
        trend: 'flat',
        accent,
      }
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

// Kalimat interpretasi "so what" per komponen untuk Summary Box modal —
// utamakan field kaya yang sudah dihitung backend, jatuh ke narrative.
export function interpretationOf(c) {
  const v = c.value || {}
  return (
    v.pattern_interpretation ||
    v.summary ||
    v.confirmation_note ||
    v.screening_implication ||
    (c.narrative ? c.narrative.split('. ').slice(-1)[0] : null) ||
    c.note ||
    '—'
  )
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
  credit_spread: 'bond',
}

export function componentIcon(key) {
  return COMPONENT_ICON[key] || 'dot'
}
