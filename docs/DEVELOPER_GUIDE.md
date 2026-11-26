# Panduan Developer — RuralLink

Panduan ini ditujukan bagi **Aditya, Zahran**, dan kontributor teknis lain untuk menjalankan server statis lokal, mereproduksi eksperimen riset Python, dan menjalankan pengujian otomatis di Windows.

## 1. Prasyarat & Setup Awal (Fresh Clone)
Website statis (`public/index.html` / `dashboard_rurallink.html`) **tidak membutuhkan Python atau dependensi apa pun** — cukup buka di browser.

Untuk menjalankan mesin riset Python (`src/`, `experiments/`, `tests/`), pastikan **Python 3.12** dan **`uv`** sudah terpasang:
```powershell
git clone https://github.com/Legorvey/rural-link.git
cd rural-link
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
```
*(Untuk versi paket yang terkunci persis pada lingkungan riset, lihat `requirements.lock.txt`.)*

## 2. Perintah Harian (Windows PowerShell)
- **Menjalankan website statis secara lokal:**
  ```powershell
  python -m http.server --directory public 8000
  ```
  Atau buka langsung `public/index.html` / `dashboard_rurallink.html` di browser.
- **Menjalankan semua tes ilmiah & environment:** `.venv\Scripts\python.exe -m pytest -q`
- **Memeriksa lint & format:**
  ```powershell
  .venv\Scripts\python.exe -m ruff check .
  .venv\Scripts\python.exe -m ruff format --check .
  ```
- **Mereproduksi grafik & CSV Fase 02–03:** `.venv\Scripts\python.exe -m experiments.run_experiments`
- **Mereproduksi grafik & CSV adaptif S0–S3 & R0:** `.venv\Scripts\python.exe -m experiments.run_adaptive`

## 3. Troubleshooting di Windows
- **`.venv` tidak memiliki `pip`:** Environment ini dikelola oleh `uv`. Selalu gunakan `uv pip install --python .venv\Scripts\python.exe ...`.
- **Error modul `src` tidak ditemukan:** Jalankan skrip menggunakan `-m` dari root repositori (mis. `python -m experiments.run_experiments`), bukan dari dalam subfolder.

## 4. Aturan Pengembangan & Integritas Ilmiah
- **HTML Freeze (`dashboard_rurallink.html` & `public/index.html`):** File HTML kanonik karya Zahran bersifat *immutable*. Jangan memodifikasi HTML/CSS/JS, menyuntikkan skrip, atau mengubah formula di dalamnya. Pastikan SHA256 kedua file tetap identik (`6a9a0ab73d9e622ccc622638e981a019f14ab00a0873ee3d371ed5afe3d89290`).
- **Jangan mengubah matematika tervalidasi:** Modul di `src/` sudah tervalidasi oleh pengujian ilmiah dan audit independen. Jika ada perubahan asumsi atau parameter di `config.py`, catat terlebih dahulu di [docs/DECISIONS.md](DECISIONS.md) dan perbarui [docs/METHODOLOGY.md](METHODOLOGY.md).
- **Menambah tes ilmiah:** Tambahkan tes di `tests/test_scientific_engine.py` atau `tests/test_adaptive.py` dengan *seed* tetap dan perbandingan terhadap nilai *closed-form*.
- **File PDF Referensi:** Folder `references/*.pdf` di-gitignore demi hak cipta. Jangan pernah menghapus aturan `.gitignore` untuk `*.pdf`.
- **Branch workflow:** Lihat [CONTRIBUTING.md](../CONTRIBUTING.md).
