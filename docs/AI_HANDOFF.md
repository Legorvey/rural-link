# Panduan AI Asisten (AI Handoff) — RuralLink

Dokumen ini memungkinkan setiap anggota tim menggunakan AI asisten masing-masing tanpa memerlukan riwayat percakapan awal.

## Konteks Singkat & Aturan Wajib
- **Snapshot:** `2026-11-25` | **Baseline commit:** `88a1828`
- **Urutan baca kanonik untuk AI:** `AGENTS.md` → `docs/PROGRESS.md` → `docs/METHODOLOGY.md` → `docs/RESULTS_GUIDE.md`.
- **Aturan integritas:** AI **dilarang** mengarang angka hasil, mengklaim Fase 04–07 sudah selesai, atau mengubah asumsi di `config.py` tanpa mencatatnya di `docs/DECISIONS.md`. Semua hasil harus merujuk pada file aktual di `outputs/` dan `src/`.

---

## 4 Prompt Siap Pakai

### A. Memahami RuralLink sebagai Anggota Baru
> Baca `AGENTS.md`, `README.md`, dan `docs/RESEARCH_OVERVIEW.md`. Jelaskan kepada saya dalam Bahasa Indonesia yang ringkas: (1) masalah *uplink* di wilayah 3T, (2) bagaimana modulasi adaptif dan alokasi RB bekerja, dan (3) fase mana yang sudah selesai vs masih *pending* berdasarkan `docs/PROGRESS.md`. Jangan mengarang hasil yang belum ada.

### B. Membantu Menyusun PPT dengan Bukti Terverifikasi
> Baca `docs/TEAM_HANDOFF.md`, `docs/PRESENTATION_GUIDE.md`, dan `outputs/results/modulation_thresholds.csv`. Bantu saya menyusun draf teks slide PPT sesuai urutan 13 slide di `TEAM_HANDOFF.md`. Gunakan hanya angka dan klaim yang ada di tabel *Claim-to-Evidence*, sertakan label data (THEORETICAL / SIMULATED), dan tandai bagian Fase 04 sebagai *pending*.

### C. Membantu Menulis Analisis & Pembahasan dari CSV dan Grafik
> Baca `docs/RESULTS_GUIDE.md`, `docs/METHODOLOGY.md`, `outputs/results/link_budget_validation.csv`, dan `outputs/results/ber_validation.csv`. Bantu saya menulis bagian Analisis & Pembahasan untuk grafik di `outputs/figures/`. Bedakan dengan jelas antara hasil teoretis dan simulasi Monte Carlo, jelaskan perbedaan $E_b/N_0$ dan $E_s/N_0$, serta cantumkan batasan ilmiah yang ada di `docs/METHODOLOGY.md`.

### D. Melanjutkan Pengembangan Kode (Tanpa Menulis Ulang Engine)
> Baca `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, dan `config.py`. Saya ingin melanjutkan pengembangan (Fase 04 `src/adaptive.py` atau Fase 05 `app.py`). Jangan menulis ulang modul `src/` yang sudah tervalidasi. Pertahankan semua asumsi di `docs/METHODOLOGY.md`, ikuti konvensi satuan, dan pastikan `.venv\Scripts\python.exe -m pytest -q` serta `ruff check .` tetap lulus.
