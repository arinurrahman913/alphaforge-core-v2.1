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
| Market Sentiment | VIX + Market Breadth + AAII + put/call | **Selalu `status=degraded`** — AAII survey & CBOE put/call belum diintegrasikan (tidak ada API resmi gratis, butuh scraping yang belum diverifikasi) |

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

## Status Implementasi

### Layer 1
- **11/12 komponen**: live (yield curve, VIX, DXY, commodities, regime, sector rotation, liquidity, macro calendar, business cycle, money flow, market breadth)
- `FRED_API_KEY` diperlukan untuk 4 komponen FRED
- `market_sentiment`: degraded (AAII survey & CBOE put/call belum integrated)

### Layer 2
- **Screening**: ✅ Jalan — 2-tahap filter (8.5K → 5.2K → ~300+ candidate), rate-limited + cached
- **Evidence**: ✅ Jalan — extended price history (1-year OHLCV), 18 fundamental fields, institutional ownership, Finnhub news, caching 24h, rate limiting
  - Features: price/market data, fundamentals (revenue, FCF, margins, ratios), institutional ownership %, company news
  - Tested: 23 ticker run ~10sec, 251 price bars/ticker, 83% with Finnhub news
- **Belum diimplementasikan**: Knowledge → Peer Comparison → Confidence → Risk/Red-Flag → 3 Reasoning Modules → Aggregator → Historical Tracking

### Dashboard
- **Layer 1 Live** (`layer1-live.html`): ✅ terhubung, membaca JSON dari pipeline
- **Evidence Live** (`evidence-live.html`): ✅ interactive table + detail modal, search/filter, 18+ fundamental fields per ticker

---

© AlphaForge v2
