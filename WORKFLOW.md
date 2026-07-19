# AlphaForge v2 — Panduan Workflow & Cara Baca Dashboard

Panduan lengkap: cara menjalankan platform, refresh data, dan **membaca setiap bagian dashboard**. Semua perintah di bawah untuk **Windows PowerShell** (shell utama kamu).

---

## 1. Apa Ini?

Dua mesin analisis saham yang berjalan berurutan:

- **Layer 1 — Market Context Engine**: 12 komponen makro (yield curve, VIX, likuiditas, dll) → satu skor kondisi pasar (`Layer Score`).
- **Layer 2 — Stock Analysis Engine**: 9 tahap per saham → Screening → Evidence → Knowledge → Peer → Confidence → Risk → Reasoning → Aggregator → Historical.

Dashboard (React) **hanya membaca file JSON** hasil pipeline — tidak menghitung ulang. Jadi alurnya selalu: **generate data → dashboard baca data**.

---

## 2. Setup Awal (sekali saja)

```powershell
# dari folder repo: H:\Project1\alphaforge-core-v2.1
pip install -r requirements.txt
npm --prefix frontend install

# FRED API key (gratis: https://fred.stlouisfed.org/docs/api/api_key.html)
# tanpa ini, 4 komponen berbasis FRED jadi status "missing"
$env:FRED_API_KEY = "MASUKKAN_KEY_KAMU"
```

> Catatan: `$env:FRED_API_KEY` hanya berlaku di sesi PowerShell yang sedang terbuka. Buka terminal baru → set lagi. (Untuk permanen: Settings → Environment Variables.)

---

## 3. Menjalankan Dashboard

Butuh **2 terminal**: backend (API) + frontend (UI).

### Terminal 1 — Backend (Flask, port 5000)
```powershell
$env:FRED_API_KEY = "MASUKKAN_KEY_KAMU"
python backend/app.py
```
Menyajikan API di `http://localhost:5000/api/<stage>` dan otomatis reload data saat file JSON berubah.

### Terminal 2 — Frontend (Vite, port 5173)
```powershell
npm --prefix frontend run dev
```
Vite mem-proxy `/api` ke backend port 5000.

### Buka
```
http://localhost:5173
```

> **Mode produksi** (opsional, satu port saja): `npm --prefix frontend run build` lalu `python backend/app.py` → buka `http://localhost:5000` (Flask menyajikan hasil build + API sekaligus).

---

## 4. Refresh Data (biar angka aktual)

Dashboard menampilkan **snapshot** — angka hanya berubah saat kamu generate ulang. Pilih sesuai kebutuhan:

### A. Layer 1 saja — cepat (~1 menit)
```powershell
$env:FRED_API_KEY = "MASUKKAN_KEY_KAMU"
python scripts/refresh_layer1.py
```
Update 10/12 komponen makro. `market_breadth` & `market_sentiment` **tidak** ikut ter-update (butuh Screening).

### B. Layer 1 lengkap 12/12 (butuh Screening dulu, ~beberapa menit)
```powershell
$env:FRED_API_KEY = "MASUKKAN_KEY_KAMU"
python -m alphaforge.cli layer1 --with-screening --screening-limit 100 --out dashboard/data/layer1_context.json
```

### C. Full pipeline — semua stage Layer 1 + Layer 2 (paling lama)
```powershell
$env:FRED_API_KEY = "MASUKKAN_KEY_KAMU"
python scripts/refresh_full_pipeline.py
```
Menjalankan Screening → Evidence → … → Aggregator + Layer 1 lengkap. Bersifat **all-or-nothing**: kalau satu stage gagal, data lama tetap dipakai (tidak menulis setengah jadi).

### Menjalankan stage tertentu manual
```powershell
python -m alphaforge.cli screening --limit 100 --out dashboard/data/screening.json
python -m alphaforge.cli evidence  --screening-out dashboard/data/screening.json --out dashboard/data/evidence.json
# stage lain: knowledge, peer, confidence, risk, reasoning, aggregator
```

Setelah refresh, **refresh browser** (Ctrl+R) untuk lihat angka baru.

---

## 5. Cara BACA Dashboard

### 5.1 Sidebar (kiri)
Navigasi antar tahap. **Market** → Layer 1. **Fase A/B** → tahap-tahap Layer 2 per saham & populasi.

### 5.2 Stat Tiles (baris atas Layer 1)
| Tile | Arti |
|---|---|
| **Layer Score** | Skor makro agregat 0–100 (rata-rata tertimbang semua komponen ok). Makin tinggi = kondisi makro makin kondusif untuk aset berisiko. |
| **Komponen** | Jumlah komponen makro (12). |
| **OK** | Komponen dengan data lengkap. |
| **Degraded** | Komponen datanya parsial/hilang. |
| **Confidence** | Keyakinan keseluruhan terhadap paket data. |

### 5.3 Bar Chart "Kontribusi ke Layer Score"
Tiap batang = seberapa besar sumbangan komponen itu ke Layer Score (skor × bobot). Batang panjang = komponen berbobot besar & skor tinggi.

### 5.4 Kartu Komponen (anatomi)
Tiap kartu Layer 1 dibaca begini:

```
┌────────────────────────────────────────┐
│ [icon]  NAMA_KOMPONEN          [ pill ] │  ← pill: ok (emas) / degraded (cyan)
│         HERO VALUE  unit                │  ← angka utama, REAL
│ ▲ Delta badge                           │  ← arah: ▲hijau naik ▼merah turun ◆emas netral
│ Stat1  Stat2  Stat3                     │  ← mini-stats pendukung, REAL
│ ╱╲___ sparkline ___╱                    │  ← DEKORATIF (arah saja, bukan histori asli)
│ Narasi singkat penjelasan…              │
│ conf 85% · acceptable · 1 konflik       │  ← confidence, freshness, jml konflik
└────────────────────────────────────────┘
```

**Klik kartu** → modal detail lengkap: Reasoning, Rule, Thresholds, Evidence (sumber tiap angka + tanggal), dan Note.

**Warna:** emas = komponen sehat (ok). Cyan = degraded (data parsial). Delta hijau/merah hanya menandai **arah** metrik, bukan bagus/buruk.

### 5.5 Membaca contoh nyata
- `yield_curve +0.37pp · Normal` → spread 10Y–2Y positif, kurva normal (tidak inverted → sinyal resesi rendah).
- `volatility_index 18.8 VIX · ▼ Di bawah avg 5th` → pasar relatif tenang.
- `market_sentiment 58/100 · degraded` → hanya 2/4 input tersedia (AAII & put/call belum ada) — baca dengan hati-hati.

### 5.6 Screening (Layer 2)
Ticker dikelompokkan per **tier market cap**: Mega (>$100B) → Large → Mid → Small → Micro (<$300M). Tiap tabel menampilkan jumlah + detail (harga, avg $volume, flags). **Klik baris** → detail per ticker. Bagian "Hard Excluded" = ticker yang gagal filter (mis. likuiditas terlalu rendah).

---

## 6. Struktur Data & API

| Endpoint | File sumber |
|---|---|
| `/api/layer1` | `dashboard/data/layer1_context.json` |
| `/api/screening` | `dashboard/data/screening.json` |
| `/api/evidence` | `dashboard/data/evidence.json` |
| `/api/ticker/<TICKER>` | gabungan semua stage untuk 1 ticker |
| `/api/ticker/<TICKER>/live` | quote live dari Yahoo (real-time, best-effort) |

---

## 7. Catatan Integritas Data

- **REAL**: semua hero value, delta, mini-stats, narasi, skor → dari **FRED API** + **Yahoo Finance**, per waktu generate.
- **DEKORATIF**: garis sparkline di kartu (mengikuti arah saja, bukan time-series 30-hari asli).
- **Proksi** (tercatat di data): `business_cycle` pakai Industrial Production (bukan ISM PMI); `money_flow` proksi volume+harga; `market_breadth` universe Screening sendiri (bukan S&P 500); `market_sentiment` degraded (2/4 input).
- **Snapshot**, bukan live-stream — update hanya saat pipeline dijalankan ulang.

---

## 8. Troubleshooting

| Gejala | Solusi |
|---|---|
| Komponen FRED "missing" | `$env:FRED_API_KEY` belum di-set di terminal backend → set lalu restart `python backend/app.py`. |
| `market_breadth` missing | Jalankan refresh opsi B atau C (`--with-screening` / full pipeline). |
| Dashboard kosong / error fetch | Pastikan backend (terminal 1) jalan di port 5000. |
| Angka tidak berubah | Refresh data (bagian 4) lalu Ctrl+R di browser. |
| Port bentrok | Ganti port backend: `$env:PORT="5001"` sebelum `python backend/app.py` (sesuaikan proxy di `frontend/vite.config.js`). |

---

## 9. Alur Singkat (cheat sheet)

```powershell
# 1. set key
$env:FRED_API_KEY = "KEY_KAMU"

# 2. refresh data (pilih salah satu)
python scripts/refresh_layer1.py                 # cepat, Layer 1 saja
python scripts/refresh_full_pipeline.py          # lengkap semua stage

# 3. jalankan (2 terminal)
python backend/app.py                            # terminal 1
npm --prefix frontend run dev                    # terminal 2

# 4. buka http://localhost:5173 → Ctrl+R setelah refresh data
```
