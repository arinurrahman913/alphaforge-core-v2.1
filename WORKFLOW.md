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
```

**FRED API key** (gratis: https://fred.stlouisfed.org/docs/api/api_key.html) — set **sekali** di file `.env`:

```powershell
Copy-Item .env.example .env
# lalu buka .env, ganti "your_fred_api_key_here" dengan key kamu
```

Setelah itu **otomatis**: backend, CLI, dan scheduled task membaca `.env` sendiri (via `python-dotenv`) — **tidak perlu** ketik `$env:FRED_API_KEY` lagi di tiap terminal. File `.env` sudah di-gitignore (tidak akan ter-commit). Tanpa key, 4 komponen berbasis FRED jadi status "missing".

---

## 3. Menjalankan Dashboard

### Paling otomatis: auto-start saat login (sudah dipasang)
Backend nyala sendiri (tanpa jendela) tiap login Windows, lewat shortcut di Startup folder yang menjalankan `scripts/start-backend-hidden.vbs`. Jadi cukup buka `http://localhost:5000` kapan saja — tidak perlu klik apa pun.

- **Mematikan sementara**: Task Manager → tab Details → hentikan `pythonw.exe` (yang jalanin backend).
- **Menonaktifkan auto-start**: hapus shortcut `AlphaForge Dashboard` di Startup folder (tekan `Win+R` → ketik `shell:startup` → Enter → hapus shortcut-nya).
- **Menyalakan ulang manual**: dobel-klik `scripts/start-backend-hidden.vbs` (hidden) atau `start-dashboard.bat` (dengan jendela).

### Cara manual: dobel-klik `start-dashboard.bat`
Setelah laptop dimatikan/restart, server dashboard ikut mati — dashboard tidak akan terbuka sampai dijalankan lagi. **Dobel-klik `start-dashboard.bat`** di root repo: backend nyala + browser otomatis kebuka di `http://localhost:5000` (mode produksi, cukup 1 proses). Biarkan jendela "AlphaForge Backend" terbuka selama dipakai; tutup jendela itu untuk mematikan. Refresh data cukup lewat tombol **Generate** di dashboard.

### Mode dev (2 terminal) — kalau sedang ngoprek kode

Butuh **2 terminal**: backend (API) + frontend (UI).

### Terminal 1 — Backend (Flask, port 5000)
```powershell
python backend/app.py
```
> FRED key otomatis dibaca dari `.env` (lihat bagian 2).
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

Dashboard menampilkan **snapshot** — angka hanya berubah saat kamu generate ulang.

### Cara termudah: tombol **Generate** di dashboard
Di pojok kanan atas dashboard ada tombol **Generate ▾** dengan 2 pilihan:
- **Refresh Layer 1** — cepat (~1 menit), update komponen makro (breadth/sentiment tidak ikut).
- **Full Pipeline** — semua stage (Layer 1 + Layer 2), lebih lama.

Klik → tombol jadi "Generating… mm:ss" (jalan di background), dan dashboard **auto-reload** saat selesai. Backend (`python backend/app.py`) harus jalan. Tidak bisa dua refresh sekaligus.

### Atau lewat terminal (pilih sesuai kebutuhan):

### A. Layer 1 saja — cepat (~1 menit)
```powershell
python scripts/refresh_layer1.py
```
Update 10/12 komponen makro. `market_breadth` & `market_sentiment` **tidak** ikut ter-update (butuh Screening).

### B. Layer 1 lengkap 12/12 (butuh Screening dulu, ~beberapa menit)
```powershell
python -m alphaforge.cli layer1 --with-screening --screening-limit 100 --out dashboard/data/layer1_context.json
```

### C. Full pipeline — semua stage Layer 1 + Layer 2 (paling lama)
```powershell
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
- `market_sentiment 50/100 · ok` → 3/4 input tersedia (vix, breadth, put/call otomatis). Tambah AAII manual (lihat 5.7) untuk 4/4.

### 5.7 Melengkapi market_sentiment jadi 4/4 (opsional — AAII manual)
`market_sentiment` otomatis `ok` begitu ≥3 dari 4 input tersedia (vix + breadth + put/call — put/call ditarik otomatis dari CNN Fear & Greed, best-effort, endpoint tidak resmi). Input ke-4, **AAII Investor Sentiment Survey**, tidak punya API gratis — isi manual:

1. Buka https://www.aaii.com/sentimentsurvey (dirilis tiap Kamis, gratis)
2. Salin `dashboard/data/sentiment_manual.json.example` → `dashboard/data/sentiment_manual.json`
3. Isi `bullish_pct`, `bearish_pct`, `as_of` dari survei terbaru
4. Generate ulang Layer 1 (tombol Generate atau `python scripts/refresh_layer1.py`)

File `sentiment_manual.json` sudah di-gitignore (spesifik-mesin, tidak ter-commit). Data kadaluarsa (>30 hari) otomatis diabaikan.

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
- **Proksi** (tercatat di data): `business_cycle` pakai Industrial Production (bukan ISM PMI); `money_flow` proksi volume+harga; `market_breadth` universe Screening sendiri (bukan S&P 500); `market_sentiment` put/call dari endpoint CNN tidak resmi (bisa putus sewaktu-waktu → komponen otomatis degrade jujur), AAII perlu diisi manual (§5.7).
- **Snapshot**, bukan live-stream — update hanya saat pipeline dijalankan ulang.

---

## 8. Troubleshooting

| Gejala | Solusi |
|---|---|
| Komponen FRED "missing" | File `.env` belum ada / key salah → `Copy-Item .env.example .env` lalu isi key, restart `python backend/app.py`. |
| `market_breadth` missing | Jalankan refresh opsi B atau C (`--with-screening` / full pipeline). |
| Dashboard kosong / error fetch | Pastikan backend (terminal 1) jalan di port 5000. |
| Angka tidak berubah | Refresh data (bagian 4) lalu Ctrl+R di browser. |
| Port bentrok | Ganti port backend: `$env:PORT="5001"` sebelum `python backend/app.py` (sesuaikan proxy di `frontend/vite.config.js`). |

---

## 9. Alur Singkat (cheat sheet)

```powershell
# 0. sekali seumur setup: Copy-Item .env.example .env  → isi FRED key

# 1. refresh data (pilih salah satu) — key otomatis dari .env
python scripts/refresh_layer1.py                 # cepat, Layer 1 saja
python scripts/refresh_full_pipeline.py          # lengkap semua stage

# 2. jalankan (2 terminal)
python backend/app.py                            # terminal 1
npm --prefix frontend run dev                    # terminal 2

# 3. buka http://localhost:5173 → Ctrl+R setelah refresh data
```
