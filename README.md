<div align="center">

<img src="docs/assets/rurallink-mark.svg" alt="Logo RuralLink: menara radio minimal dengan gelombang sinyal di atas kontur wilayah pedesaan" width="96"/>

# RuralLink

### Adaptive Uplink Coverage Simulator (700 / 900 / 1800 MHz)

*Analisis Peningkatan Jangkauan Uplink melalui Modulasi Adaptif dan Alokasi Bandwidth pada Frekuensi 900 MHz dan 1800 MHz di Wilayah 3T Indonesia.*

**Kelompok 1 — Sistem Komunikasi Digital (2026)** | Dosen Pengampu: **Bu Dessy**  
S1 Teknik Elektro FMIPA Universitas Padjadjaran

*Website statis murni tanpa backend: dapat dijalankan dari hosting statis maupun langsung offline di browser.*  
*Legacy backup (arsip Streamlit):* [`https://rural-link.streamlit.app/`](https://rural-link.streamlit.app/) *(bukan rilis aktif utama)*

[Masalah Penelitian](#permasalahan-penelitian) · [Dua Lapisan Sistem](#pemisahan-website-dan-mesin-riset) · [Fitur & Tab Website](#fitur-simulator-dan-empat-tab-aplikasi) · [Temuan Terverifikasi](#temuan-numerik-terverifikasi) · [Penggunaan Offline & Reproduksi Python](#penggunaan-offline-dan-reproduksi-riset-python) · [Tim & Kredit](#tim-dan-kredit) · [Referensi](#referensi-dan-batasan)

</div>

---

## Permasalahan Penelitian

**RuralLink** mengevaluasi batas jangkauan komunikasi *uplink* (User Equipment/UE ke Base Transceiver Station/BTS) pada wilayah pedesaan dan 3T (Tertinggal, Terdepan, Terluar) di Indonesia.

- **Kesenjangan cakupan 3T:** Laporan Kinerja Komdigi (2025) mencatat cakupan 4G Q2 2025 mencapai `98,95%` populasi, tetapi baru menjangkau `53,82%` luas wilayah daratan (dengan `6.747` lokasi BTS beroperasi di wilayah 3T).
- **Keterbatasan daya *uplink*:** Pada sel pedesaan beradius besar (`1–12 km`), daya pancar UE dibatasi `23 dBm` (`200 mW`), jauh di bawah daya pancar BTS. Akibatnya, tautan *uplink* lebih cepat mengalami *outage* saat jarak bertambah atau terjadi halangan (`NLOS` dan *shadowing*).
- **Peran alokasi *Resource Block* (`N_RB`):** Dengan daya total UE tetap, mempersempit alokasi dari `25 RB` (`4,50 MHz`) ke `1 RB` (`180 kHz`) menurunkan *noise floor* termal penerima dan menaikkan SNR teoretis sebesar **`13,98 dB`**, dengan kompromi penurunan laju data nominal.
- **Peran modulasi adaptif:** Memilih modulasi (`BPSK`, `QPSK`, `16-QAM`, `64-QAM`) sesuai kondisi kanal menjaga target $\text{BER} \le 10^{-2}$ tanpa mengorbankan laju data saat kanal dekat BTS masih baik.

---

## Pemisahan Website dan Mesin Riset

Repositori ini memisahkan secara tegas **antarmuka website statis** dan **mesin simulasi ilmiah Python**:

| Aspek | 1. Website Statis Interaktif (`public/index.html`) | 2. Mesin Riset Python (`src/` & `experiments/`) |
|---|---|---|
| **Implementasi** | HTML/CSS/JavaScript mandiri karya **Zahran** (`dashboard_rurallink.html` → `public/index.html`) | Python 3.12 (`config.py`, `src/*.py`, `experiments/*.py`) |
| **Jenis Perhitungan** | **Analitis real-time di browser** (aproksimasi `erfc` untuk kurva BER, peta radial 2D deterministik, visualisasi konstelasi 16-QAM ilustratif) | **Validasi ilmiah & Monte Carlo bit-level** (Cho–Yoon eksak, `5.000` realisasi *shared* shadowing + Rayleigh CSI, `1.000.000` bit MC, Wilson 95% CI, *hard cap* UE `23 dBm`) |
| **Backend / API** | **Tidak ada** (100% sisi klien, tanpa server, tanpa database, tanpa request eksternal) | Eksekusi luring (*offline reproducible research*) untuk menghasilkan `outputs/` |
| **Kesesuaian Hasil** | Tabel hasil di Tab 2 memuat ringkasan dari `outputs/`, sedangkan grafik & angka interaktif di Tab 1 dihitung langsung oleh JS analitis di browser | Sumber kanonik seluruh angka publikasi di `outputs/summary.md`, `outputs/results/*.csv`, dan `outputs/figures/*.png` |

> **Catatan integritas:** Website HTML menggunakan perhitungan JavaScript analitis untuk interaktivitas instan dan **tidak** menjalankan simulasi Monte Carlo *bit-level* Python secara langsung.

---

## Strategi `S0–S3` dan `R0`

| Kode | Strategi | Modulasi | Alokasi RB | Peran Evaluasi |
|---|---|---|---|---|
| **S0** | Fixed baseline | `QPSK` tetap | `25 RB` (`4,50 MHz`) tetap | Pembanding standar tanpa adaptasi |
| **S1** | Adaptive modulation | `BPSK`–`64-QAM` | `25 RB` tetap | Mengukur kontribusi adaptasi modulasi saja |
| **S2** | Adaptive bandwidth | `QPSK` tetap | `1, 2, 5, 10, 25 RB` | Mengukur kontribusi penyempitan RB saja |
| **S3** | Joint adaptive | `BPSK`–`64-QAM` | `1, 2, 5, 10, 25 RB` | Optimasi gabungan (laju nominal maks yang memenuhi target BER) |
| **R0** | Robust reference | `BPSK` tetap | `1 RB` (`180 kHz`) tetap | Referensi ketahanan maksimum pada daya UE `23 dBm` |

*(Website interaktif juga menyediakan mode `MANUAL` untuk mengunci jumlah `N_RB` pilihan pengguna.)*

---

## Fitur Simulator dan Empat Tab Aplikasi

### Cara Membuka Website
- **Langsung *offline* (tanpa server / Python):** Buka `public/index.html` atau `dashboard_rurallink.html` langsung di browser (double-click).
- **Melalui server statis lokal:**
  ```powershell
  python -m http.server --directory public 8000
  ```
  Lalu buka `http://127.0.0.1:8000/`.
- **Deployment Vercel:** Dikonfigurasi sebagai situs statis murni dengan root `public/` di [vercel.json](vercel.json) (tanpa FastAPI, tanpa Python Functions, tanpa build step, dan tanpa environment variable). URL produksi Vercel akan ditambahkan setelah deployment dikonfirmasi.

### Empat Tab Aplikasi
1. **Simulator Interaktif:** Rail parameter kiri (`700 / 900 / 1800 MHz`, skenario `S0–S3 / R0 / MANUAL`, `N_RB`, `LOS / NLOS`, `Median / Margin 95%`, `AWGN / Rayleigh`, jarak `1,0–12,0 km`, daya `20–26 dBm` untuk eksplorasi sensitivitas), tabel perbandingan lintas frekuensi, *telemetry strip* 6 metrik, grafik **Uplink SNR vs Jarak**, visualisasi **Konstelasi I/Q**, dan **Peta Zona Cakupan Radial 2D**, beserta ekspor PNG & CSV.
2. **Hasil Penelitian:** Ringkasan temuan dan tabel terverifikasi dari eksperimen Python (`adaptive_coverage_summary.csv`, `adaptive_strategy_comparison.csv`, `adaptive_mc_validation.csv`) dengan unduhan CSV.
3. **Metodologi & Batasan:** Persamaan matematis inti (Close-In path loss, link budget, derau termal, $E_b/N_0$, laju nominal), parameter model, batasan penelitian, literatur, dan kredit tim.
4. **Kamus & Persamaan (127):** Ensiklopedia 127 istilah dalam 10 kategori beserta pencarian, filter kategori, dan ekspor CSV.

---

## Temuan Numerik Terverifikasi

Seluruh nilai di bawah berasal dari eksekusi deterministik mesin Python (`experiments/run_experiments.py` dan `experiments/run_adaptive.py`, `seed = 42`, `5.000` realisasi bersama, `1.000.000` bit MC, `UE = 23 dBm`, target $\text{BER} = 10^{-2}$, target *outage* $5\%$, rentang `1–12 km`; lihat [outputs/summary.md](outputs/summary.md)):

### Validasi Teoretis & Monte Carlo (Fase 02–03)
- **Selisih path loss 1800 vs 900 MHz (THEORETICAL):** **`6,0206 dB`** ($20\log_{10}(2)$).
- **Penguatan SNR dari penyempitan RB (THEORETICAL):** `25 -> 1 RB` = **`+13,9794 dB`**; `25 -> 5 RB` = **`+6,9897 dB`**; *noise floor* `1 RB` = **`-117,447 dBm`**.
- **Ambang AWGN di $\text{BER} = 10^{-2}$ (THEORETICAL, [modulation_thresholds.csv](outputs/results/modulation_thresholds.csv)):** `BPSK` $E_b/N_0 = 4,323\text{ dB}$ ($E_s/N_0 = 4,323\text{ dB}$); `QPSK` $E_b/N_0 = 4,323\text{ dB}$ ($E_s/N_0 = 7,333\text{ dB}$); `16-QAM` $E_b/N_0 = 7,882\text{ dB}$ ($E_s/N_0 = 13,903\text{ dB}$); `64-QAM` $E_b/N_0 = 11,954\text{ dB}$ ($E_s/N_0 = 19,735\text{ dB}$).

### Perbandingan Radius Cakupan (km) ([adaptive_coverage_summary.csv](outputs/results/adaptive_coverage_summary.csv))
| Frekuensi & Lingkungan | S0 (Median PL / Shadowing / +Rayleigh CSI) | S3 (Median PL / Shadowing / +Rayleigh CSI) | R0 (Median PL / Shadowing / +Rayleigh CSI) |
|---|---|---|---|
| **900 MHz LOS** | `>=12` / `8,75` / `3,5` | `>=12` / `>=12` / `>=12` | `>=12` / `>=12` / `>=12` |
| **900 MHz NLOS** | `3,25` / `<1` / `<1` | `>=12` / `3` / `1,75` | `>=12` / `3` / `1,75` |
| **1800 MHz LOS** | `8,25` / `4,75` / `1,75` | `>=12` / `>=12` / `11,25` | `>=12` / `>=12` / `11,25` |
| **1800 MHz NLOS** | `2` / `<1` / `<1` | `9,25` / `1,5` / `1` | `9,25` / `1,5` / `1` |

*(Label: `Median PL` = **THEORETICAL**; `Shadowing` dan `Shadowing + Rayleigh CSI` = **SIMULATED** dengan target outage $\le 5\%$. Nilai `<1 km` berarti gagal di titik uji awal 1 km; `>=12 km` berarti tersensor kanan di batas rentang evaluasi.)*

### Kinerja Tepi Sel pada NLOS `2 km` (Shadowing + Rayleigh CSI, **SIMULATED**)
- **900 MHz NLOS (`2 km`):** `S0` *outage* **`38,9%`** (laju efektif `5,50 Mbit/s`) $\rightarrow$ `S3` menekan *outage* menjadi **`5,7%`** sambil mempertahankan laju efektif **`11,97 Mbit/s`** (dibanding `R0`: *outage* `5,7%`, laju efektif `0,17 Mbit/s`).
- **1800 MHz NLOS (`2 km`):** `S0` *outage* **`57,8%`** (laju efektif `3,79 Mbit/s`) $\rightarrow$ `S3` menekan *outage* menjadi **`12,0%`** dengan laju efektif **`7,79 Mbit/s`** (dibanding `R0`: `12,0%`, `0,16 Mbit/s`).

### Batasan Penelitian
- Model bersifat *link-level* tanpa *channel coding* (FEC), tanpa interferensi antar-sel, tanpa *power control* penuh, dan tanpa penjadwalan multi-user; laju nominal (`B_active * log2(M)`) bukan *throughput* jaringan LTE aktual.
- Parameter CI (`n`, `sigma`) diekstrapolasi dari kampanye pengukuran 1400 MHz di Korea Selatan (Park et al., 2023) dan belum dikalibrasi dengan data pengukuran lapangan wilayah 3T Indonesia.
- Visualisasi zona 2D bersifat radial hipotetis tanpa peta elevasi medan; estimasi jangkauan yang mencapai `12 km` bersifat tersensor kanan (`>=12 km`).
- Frekuensi `700 MHz` dan daya `>23 dBm` pada HTML interaktif bersifat eksploratori/demonstratif; eksperimen Python kanonik hanya mengevaluasi `900/1800 MHz` dengan batas keras UE `<= 23 dBm`.

---

## Penggunaan Offline dan Reproduksi Riset Python

### Prasyarat & Setup Python 3.12 (`uv`)
```powershell
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
```

### Menjalankan Eksperimen dan Pengujian
```powershell
# Reproduksi hasil Fase 02-03 (CSV & grafik PNG)
.venv\Scripts\python.exe -m experiments.run_experiments

# Reproduksi hasil adaptif S0-S3 & R0 Fase 04-06
.venv\Scripts\python.exe -m experiments.run_adaptive

# Validasi test ilmiah & linter
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

### Struktur Repositori
```text
rural-link/
├── dashboard_rurallink.html   # File HTML kanonik karya Zahran (immutable, siap pakai offline)
├── public/                    # Root deployment statis Vercel
│   ├── index.html             # Salinan identik byte-for-byte dari dashboard_rurallink.html
│   └── favicon.ico            # Favicon resmi dari aset logo RuralLink
├── vercel.json                # Konfigurasi hosting statis murni (outputDirectory: public)
├── config.py                  # Parameter default & validasi penelitian Python
├── src/                       # Mesin simulasi ilmiah Python (propagation, link_budget, modulation, channels, metrics, adaptive)
├── experiments/               # Skrip reproduksi eksperimen deterministik
├── outputs/                   # Hasil terverifikasi: summary.md, results/*.csv, figures/*.png
├── tests/                     # Pengujian otomatis ilmiah & environment (pytest)
├── glossary_data.py           # Dataset kamus 127 istilah penelitian
└── docs/                      # Dokumentasi metodologi, referensi, hasil, demo, dan tata kelola tim
```

---

## Tim dan Kredit

**Kelompok 1 — Sistem Komunikasi Digital (2026)**

| Anggota | Tanggung Jawab |
|---|---|
| **Yusril** | Presentasi / PPT |
| **Rizqul** | Presentasi / PPT |
| **Baihaqy** | Analisis dan diskusi |
| **Jeyd** | Analisis dan diskusi |
| **Aditya** | Program dan simulasi |
| **Zahran** | Program dan simulasi (termasuk aplikasi HTML statis kanonik `dashboard_rurallink.html`) |

---

## Referensi dan Batasan

- **Reddy et al. (2022)** — *Uplink coverage enhancements for extremely large-cell sites*, *EURASIP J. Wireless Commun. Netw.*, DOI: `10.1186/s13638-022-02133-3`.
- **Khan et al. (2025)** — *Optimizing adaptive modulation technique using standard propagation model for enhanced wireless communication channels*, *Scientific Reports*, DOI: `10.1038/s41598-025-16743-6` (digunakan untuk kerangka BER target $10^{-2}$; persamaan Gray-coded BER mengikuti Cho & Yoon 2002).
- **Park et al. (2023)** — *Measurement-based Close-in Path Loss Modeling with Diffraction for Rural Long-distance Communications*, *IEEE Wireless Commun. Lett.* / `arXiv:2305.01152v1`.
- **Cho & Yoon (2002)** — *On the general BER expression of one- and two-dimensional amplitude modulations*, *IEEE Trans. Commun.*, DOI: `10.1109/TCOMM.2002.1006557`.
- **Yogapratama et al. (2015)** — Parameter link budget LTE pedesaan 900/1800 MHz (Tabel IV; catatan verifikasi di [docs/REFERENCES.md](docs/REFERENCES.md)).
- **Kementerian Komdigi RI (2025)** — *Laporan Kinerja 2025* (cakupan 4G Q2 2025 dan BTS 3T).

**Sumber daya terkait:** [Metodologi Matematis](docs/METHODOLOGY.md) · [Referensi Lengkap](docs/REFERENCES.md) · [Ringkasan Hasil](outputs/summary.md) · [Panduan Hasil](docs/RESULTS_GUIDE.md) · [Panduan Demo](docs/DEMO_GUIDE.md) · [Sitasi](CITATION.cff)
