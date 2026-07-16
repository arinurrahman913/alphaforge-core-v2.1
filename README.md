# AlphaForge Core v2

Implementasi kode AlphaForge v2 (Layer 1 — Market Context Engine, Layer 2 — Stock Analysis Engine). Spec lengkap ada di repo terpisah [`alphaforge-v2-main`](https://github.com/arinurrahman913/alphaforge-v2).

## Isi Repo

- `alphaforge/layer1/` — Market Context Engine, 12 komponen sesuai `02_LAYER1_SPECS/`. Lihat §Layer 1 di bawah.
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

## Status Keseluruhan

- **Layer 1**: 10/12 komponen menghasilkan data live begitu `FRED_API_KEY` diset. 2 komponen (`market_breadth`, `market_sentiment`) sengaja degraded/missing sampai Screening (Layer 2) ada — bukan bug, konsekuensi dari D-05 di spec.
- **Layer 2** (Screening → Evidence → Knowledge → Peer → Confidence → Risk/Red-Flag → 3 modul reasoning → Aggregator → Historical Tracking): belum diimplementasikan.
- Dashboard belum dihubungkan ke output pipeline asli (masih pakai data contoh hardcoded).

---

© AlphaForge v2
