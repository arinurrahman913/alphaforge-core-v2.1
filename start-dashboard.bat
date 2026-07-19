@echo off
title AlphaForge Dashboard
cd /d "%~dp0"

echo ============================================
echo   AlphaForge v2 - Menjalankan dashboard...
echo ============================================
echo.

REM Jalankan backend (Flask). Mode produksi: Flask sekaligus menyajikan
REM frontend hasil build + API di http://localhost:5000 (cukup 1 proses).
start "AlphaForge Backend" cmd /k python backend\app.py

echo Menunggu backend siap...
timeout /t 3 /nobreak >nul

REM Buka dashboard di browser default.
start "" "http://localhost:5000"

echo.
echo  Dashboard: http://localhost:5000
echo.
echo  - Jendela "AlphaForge Backend" biarkan TERBUKA selama dipakai.
echo  - Untuk mematikan dashboard: tutup jendela backend itu.
echo  - Refresh data cukup lewat tombol "Generate" di dashboard.
echo.
timeout /t 5 /nobreak >nul
