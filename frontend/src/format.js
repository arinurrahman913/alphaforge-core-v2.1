// Formatters ported from dashboard/alphaforge.html — keep behavior identical.

export function fmtPct(v, digits = 1) {
  return v === null || v === undefined ? '—' : `${v >= 0 ? '+' : ''}${v.toFixed(digits)}%`
}

export function fmtNum(v, digits = 1) {
  return v === null || v === undefined ? '—' : v.toFixed(digits)
}

export function fmtMoney(v) {
  if (v === null || v === undefined) return '—'
  const a = Math.abs(v)
  if (a >= 1e9) return `$${(v / 1e9).toFixed(2)}B`
  if (a >= 1e6) return `$${(v / 1e6).toFixed(2)}M`
  return `$${v.toFixed(2)}`
}

const OK_VALUES = new Set(['ok', 'high', 'low', 'passed', 'buy', 'strong_buy'])
const WARN_VALUES = new Set(['medium', 'degraded', 'hold'])
const BAD_VALUES = new Set(['low_confidence', 'bad', 'critical', 'high_risk', 'excluded', 'sell', 'strong_sell'])

export function ratingClass(r) {
  const key = String(r).toLowerCase()
  if (OK_VALUES.has(r) || OK_VALUES.has(key)) return 'ok'
  if (WARN_VALUES.has(r) || WARN_VALUES.has(key)) return 'warn'
  if (BAD_VALUES.has(key)) return 'bad'
  return 'neutral'
}

export function clampPct(pct) {
  return Math.max(0, Math.min(100, pct || 0))
}

// Label human-readable untuk key/field yang tersimpan snake_case di data.
// Mapping eksplisit untuk istilah yang butuh kapitalisasi/akronim khusus;
// selain itu fallback generik (pisah '_', Title Case, rapikan akronim umum).
const LABEL_MAP = {
  // komponen Layer 1
  yield_curve: 'Yield Curve',
  business_cycle_stage: 'Business Cycle',
  market_regime: 'Market Regime',
  liquidity_conditions: 'Liquidity',
  market_breadth: 'Market Breadth',
  volatility_index: 'Volatility Index',
  commodity_signals: 'Commodity Signals',
  sector_rotation: 'Sector Rotation',
  money_flow: 'Money Flow',
  currency_dxy: 'Currency (DXY)',
  macro_calendar: 'Macro Calendar',
  market_sentiment: 'Market Sentiment',
  credit_spread: 'Credit Spread',
  // field evidence yang sering muncul
  distance_to_ma200_pct: 'Distance to MA200 (%)',
  gold_change_30d_pct: 'Gold Change 30D (%)',
  wti_change_30d_pct: 'WTI Change 30D (%)',
  copper_change_30d_pct: 'Copper Change 30D (%)',
  change_30d_pct: 'Change 30D (%)',
  change_90d_pct: 'Change 90D (%)',
  percentile_3y: 'Percentile (3Y)',
  percentile_5y: 'Percentile (5Y)',
  oas_pct: 'OAS (%)',
  oas_bps: 'OAS (bps)',
  oas_change_30d_bps: 'OAS Change 30D (bps)',
  momentum_30d_bps: 'Momentum 30D (bps)',
  leaders: 'Top Leaders',
  laggards: 'Top Laggards',
  pattern: 'Pattern',
  spread_10y_2y: 'Spread 10Y–2Y',
  m2_yoy_pct: 'M2 YoY (%)',
  indpro_yoy_pct: 'Industrial Production YoY (%)',
  gdp_qoq_pct: 'GDP QoQ (%)',
  unemployment_rate: 'Unemployment Rate',
  fed_balance_sheet_change: 'Fed Balance Sheet Δ',
  pct_above_ma200: '% Above MA200',
  universe_size: 'Universe Size',
  median_5y: 'Median (5Y)',
  score_0_100: 'Score (0–100)',
}

const ACRONYMS = { pct: '%', ma: 'MA', vix: 'VIX', dxy: 'DXY', wti: 'WTI', oas: 'OAS', gdp: 'GDP', m2: 'M2', spx: 'SPX', bps: 'bps', yoy: 'YoY', qoq: 'QoQ' }

export function prettyLabel(key) {
  if (key == null) return '—'
  const raw = String(key)
  if (LABEL_MAP[raw]) return LABEL_MAP[raw]
  return raw
    .split('_')
    .map((w) => ACRONYMS[w] || (w ? w.charAt(0).toUpperCase() + w.slice(1) : w))
    .join(' ')
}
