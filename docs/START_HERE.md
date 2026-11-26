# Mulai Dari Sini — Onboarding Tim RuralLink

Selamat datang di **RuralLink** (Proyek Kelompok 1 — Sistem Komunikasi Digital, 2026). Dokumen ini membantu seluruh 6 anggota tim (**Yusril, Rizqul, Baihaqy, Jeyd, Aditya, Zahran**) menemukan informasi yang tepat tanpa harus membaca seluruh kode.

## 1. Jalur Baca Cepat

- **Jalur 5 Menit (Semua Anggota):**
  1. Baca ringkasan masalah, temuan, dan cara membuka website di [README.md](../README.md).
  2. Cek status terbaru di [docs/PROGRESS.md](PROGRESS.md).
- **Jalur 15 Menit (Pemahaman Utuh):**
  1. Baca [docs/RESEARCH_OVERVIEW.md](RESEARCH_OVERVIEW.md) untuk narasi lengkap dari masalah hingga metode.
  2. Buka [docs/GLOSSARY.md](GLOSSARY.md) jika menemui istilah teknis seperti *Close-In*, *Resource Block*, atau *Rayleigh*.
- **Jalur Tim PPT (Yusril & Rizqul):**
  1. Baca [docs/TEAM_HANDOFF.md](TEAM_HANDOFF.md) (urutan slide & tabel *claim-to-evidence*).
  2. Pelajari [docs/DEMO_GUIDE.md](DEMO_GUIDE.md) dan [docs/PRESENTATION_GUIDE.md](PRESENTATION_GUIDE.md) untuk alur demo website statis serta 20 pertanyaan Q&A.
- **Jalur Tim Analisis & Laporan (Baihaqy & Jeyd):**
  1. Baca [docs/RESULTS_GUIDE.md](RESULTS_GUIDE.md) untuk cara membaca grafik PNG dan file CSV di `outputs/`.
  2. Gunakan [outputs/summary.md](../outputs/summary.md), [docs/TEAM_HANDOFF.md](TEAM_HANDOFF.md), dan [docs/REFERENCES.md](REFERENCES.md) sebagai rujukan sitasi dan angka terverifikasi.
- **Jalur Tim Program (Aditya & Zahran):**
  1. Baca [docs/DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) dan [docs/ARCHITECTURE.md](ARCHITECTURE.md).
  2. Pelajari [docs/METHODOLOGY.md](METHODOLOGY.md) sebelum memodifikasi mesin riset Python (`src/`).

## 2. Status Proyek Saat Ini

| Komponen | Status | Lokasi |
|---|---|---|
| Website statis kanonik karya Zahran (4 tab, offline-ready) | ✅ Aktif (frozen HTML) | `dashboard_rurallink.html`, `public/index.html` |
| Mesin ilmiah & validasi Monte Carlo (`config.py`, `src/`) | ✅ Selesai & tervalidasi | `src/`, `tests/` |
| Eksperimen S0–S3 & R0 + grafik/CSV publikasi | ✅ Tersedia (seed 42) | `experiments/`, `outputs/` |
| Arsip rilis FastAPI & Streamlit sebelumnya | 📦 Diarsipkan di Git | Tag `archive/*` |

## 3. Akses Repositori & File Referensi
- Repositori kode: `https://github.com/Legorvey/rural-link`
- File PDF referensi di `references/` **tidak** di-upload ke GitHub demi kepatuhan hak cipta. Ringkasan terverifikasinya tersedia di [docs/REFERENCES.md](REFERENCES.md).
- Arsip rilis Streamlit & FastAPI sebelumnya tetap tersimpan di riwayat Git (`archive/scientific-app`, `archive/interactive-workbench`, `archive/final-integration`, `archive/native-web`).
