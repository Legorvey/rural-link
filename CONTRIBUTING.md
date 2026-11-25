# Panduan Kontribusi & Git Workflow — RuralLink

Dokumen ini mengatur alur kerja kolaborasi untuk seluruh tim (6 anggota) agar kode ilmiah, dokumentasi, dan hasil eksperimen tetap terverifikasi.

## 1. Branch & Commit Convention
- **Default branch:** `main` (selalu dalam kondisi bersih, lulus `pytest` dan `ruff`).
- **Contoh nama branch:**
  - `feat/simulator` — pengembangan fitur engine di `src/` atau `experiments/`
  - `feat/dashboard` — pengembangan antarmuka di `app.py`
  - `docs/research-analysis` — pembaruan dokumentasi, analisis, atau materi tim
  - `fix/scientific-validation` — perbaikan bug atau validasi matematis
- **Format commit:** gunakan awalan ringkas dan deskriptif, misalnya:
  - `feat: add joint adaptive optimizer`
  - `fix: correct Rayleigh normalization`
  - `docs: update results guide`
  - `test: add closed-form BER checks`

## 2. Alur Kerja Pull Request (PR)
1. Tarik pembaruan terbaru dari `main`: `git pull origin main`
2. Buat branch baru: `git checkout -b docs/nama-fitur`
3. Lakukan perubahan secara terfokus (jangan mencampur perubahan engine ilmiah dengan perubahan UI/dokumen jika tidak perlu).
4. Jalankan pemeriksaan lokal sebelum commit:
   ```powershell
   .venv\Scripts\python.exe -m pytest -q
   .venv\Scripts\python.exe -m ruff check .
   .venv\Scripts\python.exe -m ruff format --check .
   ```
5. Push branch Anda dan buat Pull Request ke `main`.
6. **Dilarang** melakukan `git push --force` ke `main` atau menghapus riwayat commit bersama.

## 3. Penanganan Merge Conflict
- Jika terjadi konflik pada `docs/PROGRESS.md` atau `README.md`, pertahankan kedua informasi yang valid dan pastikan tidak ada status fase yang bertentangan.
- Jika konflik terjadi pada file `src/`, diskusikan dengan Aditya atau Zahran sebelum melakukan merge.

## 4. Aturan Integritas Ilmiah & Keamanan
- **Dilarang commit PDF referensi (`*.pdf`), file `.env`, API key, atau kredensial apa pun.** File PDF di `references/` sudah di-gitignore secara global.
- Setiap perubahan pada asumsi matematis atau parameter default di `config.py` **wajib** dicatat di [docs/DECISIONS.md](docs/DECISIONS.md) dan diselaraskan dengan [docs/METHODOLOGY.md](docs/METHODOLOGY.md).
- Setiap hasil baru di `outputs/` harus dihasilkan ulang secara deterministik melalui `experiments/run_experiments.py` dan diberi label data (**THEORETICAL**, **SIMULATED**, atau **ILLUSTRATIVE**).
