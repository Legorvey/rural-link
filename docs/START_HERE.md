# Mulai Dari Sini — Onboarding Tim RuralLink

Selamat datang di **RuralLink** (Proyek Kelompok 1 — Sistem Komunikasi Digital, 2026). Dokumen ini membantu seluruh 6 anggota tim (**Aditya, Zahran, Baihaqy, Jeyd, Rizqul, Yusril**) menemukan informasi yang tepat tanpa harus membaca seluruh kode.

## 1. Jalur Baca Cepat

- **Jalur 5 Menit (Semua Anggota):**
  1. Baca bagian *Baca Ini Dulu* dan *Permasalahan* di [README.md](../README.md).
  2. Cek status terbaru di [docs/PROGRESS.md](PROGRESS.md).
- **Jalur 15 Menit (Pemahaman Utuh):**
  1. Baca [docs/RESEARCH_OVERVIEW.md](RESEARCH_OVERVIEW.md) untuk narasi lengkap dari masalah hingga metode.
  2. Buka [docs/GLOSSARY.md](GLOSSARY.md) jika menemui istilah teknis seperti *Close-In*, *Resource Block*, atau *Rayleigh*.
- **Jalur Tim PPT:**
  1. Baca [docs/TEAM_HANDOFF.md](TEAM_HANDOFF.md) (termasuk urutan slide yang disarankan & tabel *claim-to-evidence*).
  2. Pelajari [docs/PRESENTATION_GUIDE.md](PRESENTATION_GUIDE.md) untuk alur demo dan 20 pertanyaan Q&A.
- **Jalur Tim Analisis & Laporan:**
  1. Baca [docs/RESULTS_GUIDE.md](RESULTS_GUIDE.md) untuk cara membaca grafik PNG dan file CSV.
  2. Gunakan [docs/TEAM_HANDOFF.md](TEAM_HANDOFF.md) dan [docs/REFERENCES.md](REFERENCES.md) sebagai rujukan sitasi.
- **Jalur Developer (Aditya & Zahran):**
  1. Baca [docs/DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) dan [docs/ARCHITECTURE.md](ARCHITECTURE.md).
  2. Pelajari [docs/METHODOLOGY.md](METHODOLOGY.md) sebelum mengubah kode atau memulai Fase 04.

## 2. Status Proyek Saat Ini

| Komponen | Status | Lokasi |
|---|---|---|
| Environment, `config.py`, dan `src/` (Fase 01–03) | ✅ Selesai & tervalidasi (77 tes lulus) | `src/`, `tests/` |
| Grafik validasi & CSV awal (4 PNG, 3 CSV) | ✅ Tersedia | `outputs/figures/`, `outputs/results/` |
| Optimasi adaptif S0–S3 (`src/adaptive.py`, Fase 04) | ⏳ Menunggu otorisasi | `src/adaptive.py` |
| Dashboard Streamlit penuh (Fase 05) & Deployment (Fase 07) | ⏳ Pending | `app.py` |

## 3. Akses Repositori & File Referensi
- Repositori kode: `https://github.com/Legorvey/rural-link` (jika bersifat *private*, minta akses kolaborator ke pemilik repositori).
- File PDF referensi di `references/` **tidak** ikut di-upload ke GitHub demi kepatuhan hak cipta. Ringkasan terverifikasinya sudah tersedia di [docs/REFERENCES.md](REFERENCES.md); jika membutuhkan PDF asli, minta melalui saluran internal kelompok.
- Pertanyaan teknis atau koordinasi pembagian tugas dapat disampaikan langsung di grup koordinasi Kelompok 1.
