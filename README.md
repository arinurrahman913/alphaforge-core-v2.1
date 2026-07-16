# AlphaForge Core v2

Implementasi kode AlphaForge v2 (Layer 1 — Market Context Engine, Layer 2 — Stock Analysis Engine). Spec lengkap ada di repo terpisah [`alphaforge-v2-main`](https://github.com/arinurrahman913/alphaforge-v2).

## Isi Repo

- `alphaforge/layer1/` — Market Context Engine, 12 komponen sesuai `02_LAYER1_SPECS/`. Lihat §Layer 1 di bawah.
- `alphaforge/layer2/` — Screening (tahap pertama Layer 2), lihat §Layer 2 di bawah.
- `alphaforge/cache.py` — cache lokal berbasis file (`.cache/`, gitignored) dengan TTL, dipakai Screening.
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

## Layer 2 — Screening

Tahap pertama Layer 2 (`03_LAYER2_SPECS/01_SCREENING.md`): menyaring seluruh NASDAQ+NYSE
jadi kandidat yang layak diproses ke Evidence.

```
python -m alphaforge.cli screening                  # full market (~5.000+ ticker, lama)
python -m alphaforge.cli screening --limit 200       # testing, subset kecil
python -m alphaforge.cli screening --out screening.json
```

Dua tahap filter:
1. **Cheap filter** (nol panggilan API) — exclude ETF, test issue, tipe bukan common stock (warrant/right/unit/preferred), langsung dari kolom listing file NASDAQ Trader.
2. **Hard exclude/soft flag** (butuh harga & market cap via Yahoo Finance, di-batch + cache) — market cap < $30jt, avg dollar volume 20 hari < $300rb, harga < $0.50, histori < 20 hari → hard exclude. Micro/small-cap, recent IPO, ADR, low liquidity → soft flag, tetap lolos.

Supaya `market_breadth` (Layer 1) bisa terisi, jalankan Layer 1 dengan `--with-screening`:

```
python -m alphaforge.cli layer1 --with-screening --screening-limit 500 --out dashboard/data/layer1_context.json
```

`--screening-limit` membatasi jumlah ticker yang di-scan (full market tanpa limit bisa
makan waktu lama karena rate-limit Yahoo Finance — lihat `04_DATA_SOURCES/05_RATE_LIMIT_CACHING_STRATEGY.md`).
Tanpa `--with-screening`, `market_breadth` tetap `status=missing` seperti sebelumnya.

### Yang belum diimplementasikan di Screening

- Kolom "ketersediaan data fundamental" (laporan kuartalan 2 kuartal terakhir) — hard
  exclude ini belum dicek; spec menyebutnya tapi butuh panggilan tambahan per ticker
  yang belum dipasang.
- Ambang belum dikalibrasi ke funnel riil skala penuh (spec sendiri menyebut ini perlu divalidasi saat implementasi).

## Status Keseluruhan

- **Layer 1**: 11/12 komponen live begitu `FRED_API_KEY` diset + Screening dijalankan (`--with-screening`). `market_sentiment` selalu `degraded` sampai AAII survey & CBOE put/call diintegrasikan.
- **Layer 2**: Screening jalan. Evidence → Knowledge → Peer → Confidence → Risk/Red-Flag → 3 modul reasoning → Aggregator → Historical Tracking belum diimplementasikan.
- Dashboard (`dashboard/layer1-live.html`) sudah terhubung ke output pipeline asli.

---

© AlphaForge v2
