# AlphaForge Core v2

Implementasi kode AlphaForge v2 (Layer 1 — Market Context Engine, Layer 2 — Stock Analysis Engine). Spec lengkap ada di repo terpisah [`alphaforge-v2-main`](https://github.com/arinurrahman913/alphaforge-v2).

## Isi Repo

- `alphaforge/layer1/` — Market Context Engine, 12 komponen sesuai `02_LAYER1_SPECS/`. Lihat §Layer 1 di bawah.
- `alphaforge/layer2/` — Stock Analysis Engine: Screening (tahap 1), Evidence (tahap 2). Lihat §Layer 2 di bawah.
- `alphaforge/cache.py` — cache lokal berbasis file (`.cache/`, gitignored) dengan TTL, dipakai Screening & Evidence.
- `dashboard/dashboard-mockup.html` — mockup dashboard lokal (statis, data contoh hardcoded), mengikuti spec `01_ARCHITECTURE/05_DASHBOARD_LOCAL.md`. Belum terhubung ke pipeline nyata.

## Layer 1 — Market Context Engine

### Setup

```
pip install -r requirements.txt
export FRED_API_KEY=xxxxx   # gratis: https://fred.stlouisfed.org/docs/api/api_key.html
```

Tanpa `FRED_API_KEY`, 4 komponen berbasis FRED (`yield_curve`, `liquidity_conditions`,
`macro_calendar`, `business_cycle_stage`) otomatis `status=missing` — pipeline tetap
jalan dan mengirim paket lengkap (sesuai `02_LAYER1_MARKET_CONTEXT.md` §5, "Kalau Ada
Komponen yang Gagal").

### Jalankan

```
python -m alphaforge.cli layer1                    # cetak MarketContextPackage ke stdout
python -m alphaforge.cli layer1 --out context.json  # tulis ke file
```

### Lihat di dashboard lokal

```
python -m alphaforge.cli layer1 --out dashboard/data/layer1_context.json
python -m http.server 8532 --directory dashboard
```

Buka `http://localhost:8532/layer1-live.html`. Halaman ini cuma membaca file JSON tadi
(Prinsip 2.1, `05_DASHBOARD_LOCAL.md`) — tidak menghitung ulang apa pun. Generate ulang
JSON-nya dan refresh browser untuk data terbaru.

`dashboard/dashboard-mockup.html` (data contoh hardcoded, statis) tetap ada sebagai
referensi visual untuk halaman yang belum ada datanya (Daftar Lensa, Layer 2).

### Status implementasi per komponen

| Komponen | Sumber | Status |
|---|---|---|
| Yield Curve | FRED (`T10Y2Y`) | Jalan (butuh `FRED_API_KEY`) |
| Volatility Index | Yahoo (`^VIX`) | Jalan |
| Currency/DXY | Yahoo (`DX-Y.NYB`) | Jalan |
| Commodity Signals | Yahoo (`GC=F`, `CL=F`) | Jalan |
| Market Regime | Yahoo (`^GSPC` vs MA50/MA200) | Jalan |
| Sector Rotation | Yahoo (11 sector ETF vs SPY) | Jalan |
| Liquidity Conditions | FRED (`WALCL`, `M2SL`) | Jalan (butuh `FRED_API_KEY`) |
| Macro Calendar | FRED release calendar (CPI, Employment) | Jalan (butuh `FRED_API_KEY`) |
| Business Cycle Stage | FRED (GDP QoQ, UNRATE, INDPRO sbg proksi PMI — lihat catatan di modul) | Jalan (butuh `FRED_API_KEY`) |
| Money Flow | Yahoo (volume+price proxy 11 sector ETF) | Jalan |
| Market Breadth | Cache harga universe Screening | **`status=missing`** — Screening belum diimplementasikan |
| Market Sentiment | VIX + Market Breadth + CFTC COT + FINRA short-volume + put/call + AAII | Jalan — `ok` pada ≥3/6 input; 4 otomatis resmi (VIX, breadth, CFTC, FINRA), put/call & AAII opsional manual |

## Layer 2 — Stock Analysis Engine

### Tahap 1: Screening

Tahap pertama (`03_LAYER2_SPECS/01_SCREENING.md`): menyaring seluruh NASDAQ+NYSE jadi kandidat untuk dianalisis.

```
python -m alphaforge.cli screening                  # full market (~5.000+ ticker, lama)
python -m alphaforge.cli screening --limit 200       # testing, subset kecil
python -m alphaforge.cli screening --out screening.json
```

Dua tahap filter:
1. **Cheap filter** — exclude ETF, test issue, non-common-stock (warrant/right/unit/preferred) langsung dari listing file.
2. **Hard exclude/soft flag** — market cap, liquidity, price history via Yahoo Finance (di-batch + cache). Market cap < $30jt, avg dollar volume < $300rb, harga < $0.50, histori < 20 hari → hard exclude. Micro-cap, recent IPO, ADR → soft flag, tetap lolos.

Jalankan Layer 1 dengan `--with-screening` supaya `market_breadth` komponen terisi:

```
python -m alphaforge.cli layer1 --with-screening --screening-limit 500 --out dashboard/data/layer1_context.json
```

### Tahap 2: Evidence

Tahap kedua (`03_LAYER2_SPECS/02_EVIDENCE.md`): kumpulkan fakta terverifikasi (price, fundamental, news, filing) per kandidat yang lolos Screening.

```
python -m alphaforge.cli evidence --screening-out screening.json --out evidence.json
python -m alphaforge.cli evidence --screening-out screening.json --out evidence.json --limit 50  # testing
```

Evidence mengumpulkan:
- **Price & Market Data** — OHLCV, market cap, shares outstanding, beta (Yahoo Finance)
- **Fundamental** — revenue, net income, EPS, P/E, debt/equity, current ratio, ROE, margins (Yahoo Finance)
- **Institutional Ownership** — persentase agregat (Yahoo Finance)
- **Company News** — berita terkini 30 hari terakhir (Finnhub, graceful degradation jika API key missing)
- **SEC Filings** — daftar filing (10-K, 10-Q, 8-K) — placeholder di MVP, diintegrasikan nanti

Tiap field ditandai dengan metadata: source, fetched_at timestamp, status (ok/missing/degraded).

Output: `EvidencePackage` per ticker → input untuk Knowledge (tahap 3).

### Evidence Dashboard (Monitoring)

Visualisasi interactive untuk monitor kualitas data Evidence:

```bash
python -m alphaforge.cli evidence --screening-out screening.json --out dashboard/data/evidence.json
python -m http.server 8532 --directory dashboard
```

Buka browser: `http://localhost:8532/evidence-live.html`

Features:
- **Table view**: 23+ ticker dengan price, market cap, revenue, net income, FCF, institutional ownership %, news count
- **Statistics**: total packages, avg market cap/revenue, % with news
- **Search/filter**: real-time filter by ticker
- **Detail modal**: klik row untuk lihat full fundamentals (18+ fields), 52w high/low, ownership %, recent news
- **Responsive**: light/dark theme, works desktop/mobile
- **Status badges**: track data source completeness (ok/degraded/missing)

Dashboard reads dari `dashboard/data/evidence.json` — tidak ada calculation, pure visualization (sesuai Prinsip 2.1).

## CLI Reference — Full Pipeline

### Quick Start: End-to-End on 3 Tickers

```bash
# Stage 1: Screening (filter universe)
python -m alphaforge.cli screening --limit 3 --out screening.json

# Stage 2: Evidence (collect data)
python -m alphaforge.cli evidence --screening-out screening.json --limit 3 --out evidence.json

# Stage 3: Knowledge (build profiles)
python -m alphaforge.cli knowledge --evidence-out evidence.json --limit 3 --out knowledge.json

# Stage 4: Peer Comparison
python -m alphaforge.cli peer --knowledge-out knowledge.json --limit 3 --out peer.json

# Stage 5: Confidence Scoring
python -m alphaforge.cli confidence \
  --knowledge-out knowledge.json \
  --peer-out peer.json \
  --limit 3 --out confidence.json

# Stage 6: Risk Assessment
python -m alphaforge.cli risk --knowledge-out knowledge.json --limit 3 --out risk.json

# Stage 7: Reasoning Pipeline (3 lenses)
python -m alphaforge.cli reasoning \
  --knowledge-out knowledge.json \
  --confidence-out confidence.json \
  --risk-out risk.json \
  --limit 3 --out reasoning.json

# Stage 8: Aggregator (final recommendation)
python -m alphaforge.cli aggregator \
  --knowledge-out knowledge.json \
  --peer-out peer.json \
  --confidence-out confidence.json \
  --risk-out risk.json \
  --reasoning-out reasoning.json \
  --limit 3 --out recommendations.json

# Stage 9: Historical Tracking
python -c "
import json
from alphaforge.layer2 import update_timeline, save_historical_timeline
from alphaforge.layer2.aggregator_contracts import FinalRecommendation

with open('recommendations.json') as f:
    data = json.load(f)
recs = [FinalRecommendation(**r) for r in data['recommendations']]
timelines = update_timeline({}, recs)
save_historical_timeline(timelines, 'historical.json')
print(f'Tracked {len(timelines)} tickers')
"
```

### Full Production Run (300+ tickers)

Remove `--limit` flag to run on complete screening universe:

```bash
python -m alphaforge.cli screening --out screening_prod.json
python -m alphaforge.cli evidence --screening-out screening_prod.json --out evidence_prod.json
python -m alphaforge.cli knowledge --evidence-out evidence_prod.json --out knowledge_prod.json
# ... continue for peer, confidence, risk, reasoning, aggregator
```

### View Dashboards

```bash
# Generate data
python -m alphaforge.cli screening --out dashboard/data/screening_prod.json
python -m alphaforge.cli evidence --screening-out dashboard/data/screening_prod.json --out dashboard/data/evidence_prod.json
python -m alphaforge.cli knowledge --evidence-out dashboard/data/evidence_prod.json --out dashboard/data/knowledge_prod.json
python -m alphaforge.cli peer --knowledge-out dashboard/data/knowledge_prod.json --out dashboard/data/peer_prod.json

# Start local server
python -m http.server 8765 --directory dashboard

# Open browser
http://localhost:8765/evidence-live.html
http://localhost:8765/knowledge-live.html
http://localhost:8765/peer-live.html
```

## Status Implementasi

### Layer 1
- **11/12 komponen**: live (yield curve, VIX, DXY, commodities, regime, sector rotation, liquidity, macro calendar, business cycle, money flow, market breadth)
- `FRED_API_KEY` diperlukan untuk 4 komponen FRED
- `market_sentiment`: `ok` — 4 input otomatis resmi (VIX, breadth, CFTC COT, FINRA short-volume); put/call & AAII opsional lewat input manual

### Layer 2 — Stock Analysis Engine (Complete ✅)

#### Fase A: Per-Ticker Analysis (Parallel)
- **Screening** ✅ — 2-stage filter (8.5K → 5.2K → 300+ candidates), rate-limited + cached
- **Evidence** ✅ — price (1Y OHLCV), fundamentals (18 fields), ownership, news (Finnhub)
  - Caching: 6h price, 24h fundamentals, 24h ownership
  - Rate limiting: batch 50 tickers/2sec
  - Dashboard: `evidence-live.html` with search/filter/modal
  
- **Knowledge** ✅ — 7-section profile per ticker
  - Section 1: Identity (sector, size category, flags)
  - Section 2: Financial Health (margins, balance sheet, cash flow, capex)
  - Section 3a: Competitive Structure (business model, TAM, revenue)
  - Section 3b: Competitive Momentum (segment growth, guidance, acceleration)
  - Section 4: Historical Trend (returns 1Y/3Y/5Y, volatility, beta)
  - Section 5: Ownership (institutional %, insider %, transactions)
  - Section 6: Valuation (P/E, P/S, P/B, EV/EBITDA, FCF yield)
  - Section 7: Governance (shares change, auditor changes, restatements, litigation)
  - Dashboard: `knowledge-live.html` with 7 collapsible sections

#### Fase B: Population-Dependent Analysis (Sequential)
- **Peer Comparison** ✅ — percentile positioning vs sector peers
  - Grouping: by sector, min 3 peers for calculation
  - Metrics: P/E, P/S, P/B, FCF yield, margins (gross/operating/net), ROE/ROA, D/E
  - Dashboard: `peer-live.html` with percentile heatmap
  
- **Confidence Scoring** ✅ — data quality assessment (0-100)
  - Per-category: price, fundamentals, ownership, news, governance, peer_group
  - Flags: low_sample_size_peer, insufficient_price_history, stale_data, incomplete_fundamentals
  - Output: confidence_score + confidence_rating (high/medium/low)
  
- **Risk/Red-Flag Detection** ✅ — anomaly detection
  - Governance: auditor changes, restatements, litigation, unusual filings
  - Financial: high debt (D/E >2), poor liquidity (current ratio <1), negative FCF
  - Momentum: earnings misses, guidance downgrades, volatility extremes
  - Valuation: extreme P/E (>100x), severe drawdowns (>50%)
  - Output: risk_score (0-100) + red_flags list + recommended_risk_adjustment
  
- **Reasoning Pipeline** ✅ — 3 independent analytical lenses
  - Quality Lens: fundamentals + margins + valuation (sections 1,2,3a,4,6,7)
  - Speculative Lens: momentum + volatility + insider activity (sections 1,3a,4-vol,5)
  - Multibagger Lens: growth + TAM + acceleration (sections 1,3a,3b,4,6)
  - Each lens: conviction_score (0-100) + stance (strong_buy/buy/hold/sell/strong_sell)
  - Aggregation: weighted average (Quality 40%, Speculative 30%, Multibagger 30%)
  - Divergence detection: flags when lenses disagree
  
- **Aggregator** ✅ — final recommendation combining all stages
  - Weighted scoring: Confidence 20% + Risk 25% + Reasoning 55%
  - Output: final recommendation + conviction (0-100)
  - Includes: tracking_id (UUID), next_review_date, red_flags, bull/bear case
  - Dashboard: `final_recommendations.json` (aggregated view)
  
- **Historical Tracking** ✅ — decision timeline + backtesting framework
  - Stores: recommendation_date, conviction, scores, reasoning, tracking_id
  - Outcome fields: actual_return_pct, decision_correct, accuracy_pct
  - Functions: load/update/save timeline, compare vs new, record outcomes
  - Enables backtesting: measure forecast accuracy over time

### Dashboards (Interactive Visualization)

#### Layer 1
- **layer1-live.html** ✅ — 12 market context components, sparklines, status badges

#### Layer 2 — Fase A
- **evidence-live.html** ✅ — Price/market data, 18 fundamentals, ownership %, news
  - Table: 300+ tickers with key metrics
  - Detail modal: 18 field fundamentals, 52w high/low, news headlines
  - Search/filter by ticker, statistics, data quality tracking

- **knowledge-live.html** ✅ — 7-section Knowledge profiles
  - Table: 300+ tickers with returns, volatility, P/E, institutional ownership
  - Detail modal: all 7 sections + metadata + data quality notes
  - Collapsible sections, search/filter, statistics

#### Layer 2 — Fase B (Stage 1)
- **peer-live.html** ✅ — Peer comparison + percentile positioning
  - Table: peer group size, member tickers, sample size status
  - Detail modal: peer group composition, percentile bars vs metrics
  - Warnings for low sample size, metric comparison cards

#### Pending Dashboards (Scope 2)
- confidence-live.html — data quality scores per category
- risk-live.html — red flags by severity, risk heatmap
- reasoning-live.html — 3 lens scores side-by-side
- aggregator-live.html — final recommendations with conviction + tracking

---

© AlphaForge v2
