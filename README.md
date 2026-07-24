# AlphaForge Core v2

Implementasi kode AlphaForge v2 — dua mesin analisis saham:

- **Layer 1 — Market Context Engine**: 13 komponen makro (yield curve, VIX, likuiditas, credit spread, dll) → satu skor kondisi pasar (`Layer Score`).
- **Layer 2 — Stock Analysis Engine**: 9 tahap per saham (Screening → Evidence → Knowledge → Peer → Confidence → Risk → Reasoning → Aggregator → Historical).

Spec/arsitektur lengkap (kenapa sistem ini dirancang begini) ada di repo terpisah [`alphaforge-v2-main`](https://github.com/arinurrahman913/alphaforge-v2). Repo ini adalah **implementasinya** — kalau spec dan kode berbeda, catat perbedaannya (ada beberapa yang didokumentasikan sengaja, lihat §Known Gaps), jangan langsung asumsikan salah satu paling benar.

**Kalau kamu AI/kontributor baru:** baca bagian §Arsitektur & §Data Contracts dulu sebelum menyentuh kode — bagian itu isinya "kenapa ini begini", bukan cuma "ini ada apa". Untuk **cara menjalankan sehari-hari** (refresh data, baca dashboard, troubleshooting), itu semua ada di [`WORKFLOW.md`](WORKFLOW.md) — jangan diduplikasi di sini.

---

## Arsitektur

Tiga bagian yang jalan terpisah tapi saling terhubung lewat file JSON:

```
alphaforge/          → mesin analisis murni (Python). Tidak tahu apa-apa soal web/dashboard.
  layer1/             13 komponen Market Context
  layer2/              9 tahap Stock Analysis (contracts.py per tahap + sources/ untuk fetch data eksternal)
  cli.py               CLI untuk jalankan tiap tahap manual (python -m alphaforge.cli <stage>)
  cache.py             cache lokal berbasis file (.cache/, gitignored, TTL per sumber)
  json_safe.py          serialisasi JSON yang aman dari NaN/Infinity (lihat §Known Gaps)

backend/app.py        → Flask, READ-ONLY. Cuma menyajikan dashboard/data/*.json sebagai API
                         (di-cache in-memory per mtime file — lihat _get_stage). Tidak menghitung
                         apa pun sendiri. Juga bisa TRIGGER refresh (subprocess ke scripts/) lewat
                         tombol Generate, tapi computation-nya tetap di alphaforge/, bukan di sini.

frontend/             → React + Vite. Baca API dari backend/app.py, render dashboard.
                         Build ke frontend/dist/ (tracked di git, di-serve langsung oleh Flask —
                         jadi produksi cuma butuh 1 proses: python backend/app.py).

scripts/               → orkestrasi/otomasi: refresh_full_pipeline.py (jalankan 9 tahap Layer 2 +
                         Layer 1 berurutan, all-or-nothing), refresh_layer1.py (cepat, Layer 1 saja),
                         build_sector_map.py (klasifikasi sektor per ticker, cache 90 hari, dipakai
                         screening per-sektor).

dashboard/data/*.json  → SUMBER KEBENARAN untuk apa yang ditampilkan dashboard (gitignored — hasil
                         generate, bukan kode). Kalau angka di dashboard salah, cek isi file ini
                         dulu sebelum curiga ke frontend.
```

**Alur data**: `alphaforge/` (compute) → tulis ke `dashboard/data/*.json` (lewat `scripts/refresh_*.py` atau `python -m alphaforge.cli <stage> --out ...`) → `backend/app.py` baca file itu → `frontend/` render. Tidak ada arah lain — dashboard **tidak pernah** menghitung ulang apa pun (Prinsip 2.1 di spec repo).

---

## Setup & Menjalankan

Ringkas (detail lengkap + troubleshooting ada di [`WORKFLOW.md`](WORKFLOW.md)):

```powershell
pip install -r requirements.txt
npm --prefix frontend install
Copy-Item .env.example .env   # isi FRED_API_KEY (gratis, lihat komentar di file)

# refresh data (pilih salah satu)
python scripts/refresh_layer1.py          # cepat (~1 menit), Layer 1 saja
python scripts/refresh_full_pipeline.py   # lengkap, semua stage (bisa 1-2+ jam full-market)

# jalankan dashboard
npm --prefix frontend run build           # build sekali (atau `npm run dev` untuk mode dev)
python backend/app.py                     # buka http://localhost:5000
```

Tanpa `FRED_API_KEY`, 5 komponen Layer 1 berbasis FRED otomatis `status=missing` — pipeline tetap jalan, tidak crash. Sama halnya tanpa `FINNHUB_API_KEY` (juga di `.env`, gratis di [finnhub.io/register](https://finnhub.io/register)): Evidence.news otomatis `status=missing` untuk semua ticker, bukan crash.

---

## Layer 1 — Market Context Engine

13 komponen, semua sudah live: yield curve, volatility index (VIX), currency/DXY, commodity signals, market regime, sector rotation, liquidity conditions, macro calendar, business cycle stage, money flow, market breadth, market sentiment, credit spread.

5 komponen butuh `FRED_API_KEY` (yield curve, liquidity, macro calendar, business cycle, credit spread). `market_breadth` butuh Screening pernah jalan minimal sekali (pakai cache harga hasil Screening). `market_sentiment` `ok` dengan ≥3/6 input — 4 otomatis (VIX, breadth, CFTC COT, FINRA short-volume), 2 sisanya (put/call, AAII) manual opsional.

Detail cara baca tiap komponen + anatomi kartu ada di [`WORKFLOW.md`](WORKFLOW.md) §5.

---

## Layer 2 — Stock Analysis Engine

9 tahap berurutan, tiap tahap konsumsi output tahap sebelumnya:

| # | Tahap | Modul | Ringkas |
|---|---|---|---|
| 1 | Screening | `screening.py` | Filter universe NASDAQ+NYSE (~8.500 raw → ~5.200 setelah cheap-filter) jadi kandidat: exclude ETF/test-issue, market cap/likuiditas/harga minimum. Soft-flag (micro-cap, recent-IPO, ADR) tetap lolos. |
| 2 | Evidence | `evidence.py` + `sources/` | Kumpulkan fakta mentah per ticker: price/OHLCV (Yahoo), fundamental (Yahoo), institutional ownership % + top holders (Yahoo), **institutional/insider activity dari SEC Form 4** (`sources/sec_form4.py` — lihat catatan di bawah), news (Finnhub), SEC filings 10-K/10-Q/8-K (EDGAR). |
| 3 | Knowledge | `knowledge.py` | Strukturkan Evidence jadi `KnowledgeProfile` 7-bagian (identity, financial health, competitive structure/momentum, historical trend, ownership, valuation, governance) — murni faktual, tanpa penilaian kualitatif. |
| 4 | Peer | `peer.py` | Posisi percentile vs peer sektor (P/E, P/S, margins, dll), min 3 peer untuk dihitung. |
| 5 | Confidence | `confidence.py` | `ConfidenceReport`: skor kualitas data per section (0-100) + limiters, bukan lagi single confidence_score generik. |
| 6 | Risk | `risk.py` | `RiskAssessment` dengan `Flag` (severity `tinggi`/`ekstrem`, status `triggered`/`undetermined`). Flag `ekstrem` yang `triggered` **hard-gate**: `halted=true`, ticker itu skip tahap Reasoning. |
| 7 | Reasoning | `reasoning.py` | **3 lensa independen, TIDAK diagregasi jadi satu angka** (`ModuleOutput` per lensa — lihat §Data Contracts). |
| 8 | Aggregator | `aggregator.py` | Gabungkan 3 `ModuleOutput` + `Synthesis` (peta konvergensi, bukan skor tunggal). |
| 9 | Historical | `historical.py` | Simpan snapshot utuh `AggregatorOutput` per hari per ticker (`HistoricalEntry`). Evaluasi outcome (v2.1) belum ada — lihat §Known Gaps. |

### Data Contracts — penting dibaca sebelum ubah Reasoning/Aggregator

Repo ini sudah melalui **rewrite Data-Contracts v3.0.0** (2026-07-22/23) yang mengganti arsitektur lama (single `conviction_score` + `strong_buy`/…/`strong_sell` + `FinalRecommendation`) dengan yang jauh lebih ketat:

- **`ModuleOutput`** (`reasoning_contracts.py`) — tiap lensa (`multibagger`, `quality_compound`, `speculative`) punya **kosakata stance sendiri**, bukan enum bersama:
  - Multibagger: `ruang_terbuka` / `ruang_sempit` / `ruang_tertutup` / `ruang_tak_terbaca`
  - Quality: `compounding_kuat` / `compounding_rapuh` / `bukan_compounder` / `mesin_tak_terbaca`
  - Speculative: `asimetri_berkatalis` / `asimetri_tanpa_katalis` / `tanpa_asimetri` / `asimetri_tak_terbaca`
  - `confidence` terpisah dari `stance` (bukan dicampur jadi satu angka). `validate_module_output()` menjalankan cek V1-V6 tiap pipeline (di-log, tidak menghentikan run).
- **`AggregatorOutput`** (`aggregator_contracts.py`) — **DILARANG** (D-04) punya field verdict/score/rank/recommendation tunggal. Isinya `module_outputs` (3 `ModuleOutput` apa adanya, berdampingan) + `Synthesis` (agreements/divergences/`surprise`, confidence = **terendah** dari 3 modul, bukan rata-rata). `halted=true` → `module_outputs` kosong, `synthesis=None`, tapi `risk_flags` tetap terisi.
- **`HistoricalEntry`** (`historical_contracts.py`) — simpan **snapshot utuh** `AggregatorOutput`, bukan ringkasan. `outcome` sengaja `None` (evaluasi v2.1 belum diputuskan bentuknya).

**Kalau kamu lihat kode/dokumen lama menyebut `conviction_score`, `strong_buy`, atau `FinalRecommendation` — itu SUDAH DIGANTI.** Jangan tambahkan balik pola itu.

### SEC Form 4 — Institutional/Insider Activity (baru, 2026-07-23/24)

`sources/sec_form4.py` fetch daftar Form 4 filing dari SEC EDGAR submissions API per ticker, disimpan sebagai `InstitutionalActivity` (`contracts.py`) di Evidence, lalu diringkas jadi `Ownership.insider_filing_activity_30d` (hitungan filing 30 hari terakhir) di Knowledge.

**Batasan yang harus diketahui**: ini **MVP — cuma hitungan filing, bukan parsing arah transaksi** (belum bisa bedakan insider beli vs jual, atau berapa lembar saham). Percobaan parsing XML Form 4 penuh gagal karena struktur path dokumen SEC archive tidak konsisten (404 di banyak kasus) — didokumentasikan sebagai keterbatasan yang disengaja, bukan bug tersembunyi. Sinyal ini dipakai sebagai proxy "ada insider terlibat" di 2 lensa Reasoning:
- **Quality**: +8/+15/+20 poin tergantung jumlah filing (1/2/3+)
- **Speculative**: 2+ filing dalam 30 hari **memicu** stance `asimetri_berkatalis` (diperlakukan sebagai katalis implisit — insider tidak akan filing kalau tidak melihat upside)

### Dashboard: Sector Cards (Knowledge view)

Halaman Knowledge di dashboard **tidak** menampilkan satu tabel flat 4000+ baris — tapi grid card per sektor (klik untuk expand ke tabel penuh sektor itu). Agregat per sektor (leader, opportunity count, risk flag count, dll) dihitung di endpoint backend `GET /api/knowledge/sector-summary` (`backend/app.py`), bukan di browser — karena butuh join `knowledge.json` dengan `reasoning_outputs.json`/`risk_assessments.json` yang ukurannya puluhan MB.

**Catatan penting kalau menambah statistik agregat baru di situ**: `return_1y`/`pe_ratio`/`revenue_yoy` semuanya *fat-tailed* (satu ticker naik ribuan persen menyeret rata-rata jauh dari kondisi tipikal) — pakai **median**, bukan mean, untuk metrik itu (lihat `_median()` di `backend/app.py`). `institutional_pct` aman pakai mean (dibatasi 0–100%). Nama sektor di data pakai taksonomi **Yahoo Finance mentah** (`Financial Services`, `Consumer Cyclical`, `Consumer Defensive`, `Basic Materials`), **bukan** nama GICS baku yang mirip tapi beda — jangan asumsikan `sector` field sudah GICS-clean.

---

## Known Gaps (jujur, per 2026-07-24 — cek ulang sebelum percaya, ini snapshot bukan live status)

Supaya tidak ada yang menganggap sesuatu "pasti sudah dikerjakan" padahal belum:

- **Risk**: dari 6 kategori flag (`Flag`, severity `tinggi`/`ekstrem`), cuma **dilution** yang punya jalur deteksi nyata. 5 lainnya (auditor change, restatement, litigation, insider selling, fraud/delisting) selalu `status=undetermined` — Evidence cuma nyimpen filing form_type/tanggal, bukan isi filing. Hard-gate `halted` sudah dibangun & ditest tapi belum pernah benar-benar terpicu di data nyata.
- **Reasoning**: bobot & kriteria 3 lensa masih placeholder spec ("didiskusikan terpisah, belum final") — jangan anggap angka skornya sudah dikalibrasi serius.
- **Peer**: `peer_failures` selalu `[]` (butuh Screening kirim daftar kandidat per-sektor, belum ada). `roe_comparison` sebenarnya data institutional-ownership yang salah label (tidak ada field ROE asli).
- **Aggregator**: `percentile_vs_peer` selalu `None`.
- **Historical**: evaluasi outcome (v2.1 — apakah rekomendasi lama ternyata benar) belum ada bentuknya sama sekali, `outcome` selalu `None`.
- **SEC Form 4**: lihat §SEC Form 4 di atas — cuma hitungan filing, bukan arah/volume transaksi.
- **market_breadth** (Layer 1): butuh Screening pernah jalan sekali dulu (pakai cache harganya) — kalau belum, `status=missing`.
- **`json_safe.py`**: NaN/Infinity dari pandas/JSON perlu di-null-kan manual di titik serialisasi — kalau nambah tempat tulis JSON baru ke `dashboard/data/`, pastikan lewat `dumps_safe()`, bukan `json.dumps()` biasa (pernah 3x jadi bug nyata: Layer 1 SPX MA, Screening `last_price`).

---

## Testing

Tidak ada suite pytest formal kecuali `test_quarterly_trends.py`. Verifikasi tahap lain historisnya dilakukan manual: `ast.parse()` untuk cek syntax, script smoke-test sekali pakai per perubahan (biasanya ditulis ke scratch lalu dihapus setelah verifikasi), dan validasi end-to-end di browser lewat dashboard beneran. Kalau menambah logic baru yang penting, pertimbangkan nambah test nyata — jangan cuma ikut pola lama ini karena "sudah biasa begitu".

---

© AlphaForge v2
