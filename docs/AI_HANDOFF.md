# Panduan AI Asisten (AI Handoff) — RuralLink

Dokumen ini memandu asisten AI agar selaras dengan keputusan final repositori.

## Konteks Singkat & Aturan Wajib
- **Urutan baca kanonik untuk AI:** `AGENTS.md` → `docs/PROJECT_CONTEXT.md` → `docs/DECISIONS.md` → `docs/PROGRESS.md`.
- **HTML Freeze Mutlak:** `dashboard_rurallink.html` dan `public/index.html` adalah website statis kanonik karya Zahran dan **tidak boleh dimodifikasi** (harus tetap identik *byte-for-byte*, SHA256 `6a9a0ab73d9e622ccc622638e981a019f14ab00a0873ee3d371ed5afe3d89290`).
- **Pemisahan Lapisan:** Website statis memakai JavaScript analitis di browser (*zero backend*), sedangkan `src/` dan `experiments/` adalah implementasi riset Python luring yang menghasilkan `outputs/`.
- **Aturan integritas:** AI **dilarang** mengarang angka hasil, mengubah asumsi di `config.py` tanpa mencatatnya di `docs/DECISIONS.md`, atau melemahkan tes ilmiah.

---

## 3 Prompt Siap Pakai

### A. Memahami RuralLink sebagai Anggota Baru
> Baca `AGENTS.md`, `README.md`, dan `docs/RESEARCH_OVERVIEW.md`. Jelaskan secara ringkas dalam Bahasa Indonesia: (1) masalah *uplink* di wilayah 3T, (2) bagaimana modulasi adaptif dan alokasi RB bekerja, dan (3) perbedaan antara website JS analitis (`public/index.html`) dan eksperimen Monte Carlo Python (`src/`, `outputs/`).

### B. Membantu Menyusun PPT & Analisis dengan Bukti Terverifikasi
> Baca `docs/TEAM_HANDOFF.md`, `docs/RESULTS_GUIDE.md`, dan `outputs/summary.md`. Bantu saya menyusun narasi slide/analisis menggunakan angka terverifikasi dengan label data eksplisit (`THEORETICAL` / `SIMULATED`), perbedaan $E_b/N_0$ dan $E_s/N_0$, serta batasan ilmiah di `docs/METHODOLOGY.md`.

### C. Melanjutkan Pengujian atau Eksperimen Python
> Baca `AGENTS.md`, `docs/ARCHITECTURE.md`, `docs/DEVELOPER_GUIDE.md`, dan `config.py`. Jangan mengubah `dashboard_rurallink.html`, `public/index.html`, atau modul `src/` yang sudah tervalidasi tanpa keputusan di `docs/DECISIONS.md`, dan pastikan `.venv\Scripts\python.exe -m pytest -q` serta `ruff check .` tetap lulus.
