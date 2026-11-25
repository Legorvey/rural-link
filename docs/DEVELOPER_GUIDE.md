# Panduan Developer — RuralLink

Panduan ini ditujukan bagi **Aditya, Zahran**, dan kontributor teknis lain untuk menjalankan, menguji, dan mengembangkan proyek secara mandiri di Windows.

## 1. Prasyarat & Setup Awal (Fresh Clone)
Pastikan **Python 3.12** dan **`uv`** sudah terpasang.
```powershell
git clone https://github.com/Legorvey/rural-link.git
cd rural-link
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
```
*(Untuk versi paket yang terkunci persis, lihat `requirements.lock.txt`. Untuk deployment Streamlit Cloud, gunakan `requirements.txt` dan pilih Python 3.12 di pengaturan Cloud.)*

## 2. Perintah Harian (Windows PowerShell)
- **Menjalankan semua tes:** `.venv\Scripts\python.exe -m pytest -q`
- **Memeriksa lint & format:**
  ```powershell
  .venv\Scripts\python.exe -m ruff check .
  .venv\Scripts\python.exe -m ruff format --check .
  ```
- **Mereproduksi grafik & CSV:** `.venv\Scripts\python.exe -m experiments.run_experiments`
- **Menjalankan Streamlit lokal:** `.venv\Scripts\python.exe -m streamlit run app.py`

## 3. Troubleshooting di Windows
- **`.venv` tidak memiliki `pip`:** Environment ini dikelola oleh `uv`. Selalu gunakan `uv pip install --python .venv\Scripts\python.exe ...`.
- **Error modul `src` tidak ditemukan:** Jalankan skrip menggunakan `-m` dari root repositori (mis. `python -m experiments.run_experiments`), bukan dari dalam subfolder.

## 4. Aturan Pengembangan & Integritas Ilmiah
- **Jangan mengubah matematika tervalidasi:** Modul `propagation.py`, `link_budget.py`, `modulation.py`, `channels.py`, dan `metrics.py` sudah lulus 77 tes dan audit independen. Jika ada perubahan asumsi atau parameter di `config.py`, catat terlebih dahulu di [docs/DECISIONS.md](DECISIONS.md) dan perbarui [docs/METHODOLOGY.md](METHODOLOGY.md).
- **Menambah tes ilmiah:** Tambahkan tes di `tests/test_scientific_engine.py` dengan *seed* tetap dan perbandingan terhadap nilai *closed-form*.
- **Mengubah UI (`app.py`):** Jaga agar UI tetap tipis (hanya memanggil engine dan menampilkan hasil) serta kompatibel dengan Streamlit Cloud (tanpa database atau API eksternal).
- **File PDF Referensi:** Folder `references/*.pdf` di-gitignore demi hak cipta. Jangan pernah menghapus aturan `.gitignore` untuk `*.pdf`. Anggota baru harus memperoleh PDF secara terpisah melalui saluran internal tim.
- **Branch workflow:** Selalu buat branch baru (mis. `feat/adaptive-optimizer`) sebelum mengedit kode; lihat [CONTRIBUTING.md](../CONTRIBUTING.md).
