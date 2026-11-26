<div align="center">

<img src="docs/assets/rurallink-mark.svg" alt="Logo RuralLink: menara radio minimal dengan gelombang sinyal di atas kontur wilayah pedesaan" width="96"/>

# RuralLink

### Adaptive Uplink Coverage Simulator (900 & 1800 MHz)

*Analisis Peningkatan Jangkauan Uplink melalui Modulasi Adaptif dan Alokasi Bandwidth pada Frekuensi 900 MHz dan 1800 MHz di Wilayah 3T Indonesia.*

**Kelompok 1 — Sistem Komunikasi Digital (2026)** | Dosen Pengampu: **Bu Dessy**

[**Buka Simulator Langsung: https://rural-link.streamlit.app/**](https://rural-link.streamlit.app/)

*Dapat dijalankan langsung di browser tanpa menginstal Python.*

[Ringkasan Penelitian](#ringkasan-penelitian) · [Cara Kerja](#cara-kerja-rurallink) · [Temuan Utama](#temuan-utama-penelitian) · [Cara Menggunakan](#cara-menggunakan-website) · [Tim & Tanggung Jawab](#tim-dan-tanggung-jawab) · [Pusat Sumber Daya Tim](#pusat-sumber-daya-tim) · [Dokumentasi Teknis](#dokumentasi-teknis) · [Referensi & Batasan](#referensi-dan-batasan)

</div>

---

## Ringkasan Penelitian

**RuralLink** adalah simulator *link-level* berbasis Python untuk mengevaluasi batas jangkauan komunikasi *uplink* (perangkat pengguna/UE ke menara BTS) pada wilayah pedesaan dan 3T (Terdepan, Terluar, Tertinggal) di Indonesia.

- **Masalah konektivitas 3T:** Pada sel pedesaan yang luas, daya pancar UE dibatasi maksimal `23 dBm` (sekitar 200 mW), jauh lebih kecil daripada daya pancar BTS. Akibatnya, koneksi *uplink* lebih dulu mengalami *outage* saat jarak bertambah atau terjadi halangan (*NLOS* / *shadowing*).
- **Mengapa mengurangi bandwidth aktif menaikkan SNR:** Jika daya pancar UE tetap (`23 dBm`) difokuskan ke jumlah *Resource Block* (`N_RB`) yang lebih sedikit (misalnya dari `25 RB` menjadi `1 RB`), *noise floor* termal turun dan energi per simbol meningkat. Pengurangan `25 -> 1 RB` memberi penguatan SNR teoretis sebesar `13,98 dB` dengan mengorbankan laju data nominal.
- **Mengapa modulasi adaptif berguna:** Saat kanal baik (dekat BTS), UE memakai `64-QAM` atau `16-QAM` untuk laju tinggi. Saat kanal memburuk (tepi sel), UE turun ke `QPSK` atau `BPSK` agar target `BER <= 1e-2` tetap terjaga.
- **Tujuan penelitian:** Membandingkan jangkauan, probabilitas *outage*, dan laju nominal efektif antara strategi tetap (`S0`, `R0`) dan adaptif (`S1`, `S2`, `S3`) pada frekuensi `900 MHz` dan `1800 MHz` (lingkungan `LOS` dan `NLOS`, rentang `1–12 km`).

---

## Cara Kerja RuralLink

```mermaid
flowchart LR
    A["Parameter RF<br/>(900/1800 MHz, UE <=23 dBm)"] --> B["Propagasi CI<br/>(LOS/NLOS + Shadowing)"]
    B --> C["Link Budget<br/>(Pr, Noise, SNR, Eb/N0)"]
    C --> D["Kanal & CSI<br/>(AWGN / Rayleigh)"]
    D --> E["Optimasi Modulasi & RB<br/>(S0-S3, R0; BER <= 1e-2)"]
    E --> F["Evaluasi Kinerja<br/>(Outage, Radius, Rate, MC)"]
```

### Strategi yang Dibandingkan

Semua skenario dievaluasi menggunakan realisasi *shadowing* dan *Rayleigh fading* yang sama (*shared realizations*, `5.000` realisasi per titik jarak, `seed = 42`):

| Kode | Strategi | Modulasi | Alokasi RB | Peran dalam Penelitian |
|---|---|---|---|---|
| **S0** | Fixed baseline | `QPSK` tetap | `25 RB` (`4,50 MHz`) tetap | Pembanding standar tanpa adaptasi |
| **S1** | Adaptive modulation | `BPSK`–`64-QAM` | `25 RB` tetap | Mengukur efek adaptasi modulasi saja |
| **S2** | Adaptive bandwidth | `QPSK` tetap | `1, 2, 5, 10, 25 RB` | Mengukur efek penyempitan RB saja |
| **S3** | Joint adaptive | `BPSK`–`64-QAM` | `1, 2, 5, 10, 25 RB` | Optimasi gabungan (laju nominal maks yang layak) |
| **R0** | Robust reference | `BPSK` tetap | `1 RB` (`180 kHz`) tetap | Batas ketahanan maksimum pada daya 23 dBm |

---

## Temuan Utama Penelitian

Seluruh angka di bawah berasal langsung dari [outputs/summary.md](outputs/summary.md) (`UE 23 dBm`, `BER target 1e-2`, `outage target 5%`, rentang `1–12 km`).

- **Cara membedakan metrik:**
  - **Radius Median PL (THEORETICAL):** Jarak maksimum tanpa *shadowing* (`X_sigma = 0`). Bersifat deterministik dan **bukan** ukuran keandalan.
  - **Radius Andal 95% (SIMULATED):** Jarak maksimum dengan probabilitas *outage* `<= 5%` di bawah *shadowing* log-normal (dan *Rayleigh fading* dengan CSI sesaat). Nilai `<1 km` berarti titik uji pertama (`1 km`) sudah melampaui target *outage*; `>=12 km` berarti tersensor kanan oleh batas rentang uji.
  - **Laju Nominal Efektif (SIMULATED):** Laju tidak terkode `B_active * log2(M)` yang dirata-ratakan atas seluruh realisasi dengan *outage* dihitung `0`. Nilai ini **bukan** *throughput* aktual jaringan LTE.
  - **BER Bersyarat vs BER Rata-rata Rayleigh:** Pada adaptasi CSI sesaat, link hanya mengirim saat `Eb/N0` sesaat memenuhi ambang AWGN, sehingga BER bersyarat maksimum adalah `1,00e-2`. Angka BER Rayleigh `4–7%` pada tabel validasi Monte Carlo adalah BER rata-rata **tanpa CSI** pada modulasi yang dipilih dari SNR lambat.

### Perbandingan Radius Cakupan (km)

| Frekuensi & Lingkungan | S0 (Fixed) Median / Andal + Fading | S3 (Joint) Median / Andal + Fading | R0 (1 RB) Median / Andal + Fading |
|---|---|---|---|
| **900 MHz LOS** | `>=12 km` / `3,5 km` | `>=12 km` / `>=12 km` | `>=12 km` / `>=12 km` |
| **900 MHz NLOS** | `3,25 km` / `<1 km` | `>=12 km` / `1,75 km` | `>=12 km` / `1,75 km` |
| **1800 MHz LOS** | `8,25 km` / `1,75 km` | `>=12 km` / `11,25 km` | `>=12 km` / `11,25 km` |
| **1800 MHz NLOS** | `2 km` / `<1 km` | `9,25 km` / `1 km` | `9,25 km` / `1 km` |

### Contoh Kinerja Tepi Sel (NLOS, Jarak `2 km`, Shadowing + Rayleigh CSI)

| Frekuensi | S0 Outage / Laju Efektif | S3 Outage / Laju Efektif | R0 Outage / Laju Efektif |
|---|---|---|---|
| **900 MHz NLOS** | `38,9%` / `5,50 Mbit/s` | `5,7%` / `11,97 Mbit/s` | `5,7%` / `0,17 Mbit/s` |
| **1800 MHz NLOS** | `57,8%` / `3,79 Mbit/s` | `12,0%` / `7,79 Mbit/s` | `12,0%` / `0,16 Mbit/s` |

**Makna praktis:** Optimasi gabungan (`S3`) menyamai keandalan batas bawah `R0` (`5,7%` pada 900 MHz NLOS 2 km), tetapi tetap mempertahankan laju nominal efektif `11,97 Mbit/s` dibanding `0,17 Mbit/s` pada `R0` dan `5,50 Mbit/s` pada `S0`.

---

## Cara Menggunakan Website

Buka [https://rural-link.streamlit.app/](https://rural-link.streamlit.app/) di browser:

1. Klik **Preset: pemulihan tepi sel** di panel kiri (`900 MHz`, `NLOS`, `5,0 km`, `23 dBm`, strategi `S3`, target BER `1e-2`).
2. Amati seluruh instrumen utama dalam satu halaman **A. Workbench interaktif**: *telemetry strip*, grafik **SNR vs jarak** dengan penanda jarak aktif, **peta zona modulasi radial sisi-ke-sisi**, tabel **Fixed vs adaptif**, dan tabel **Perbandingan frekuensi**.
3. Bandingkan frekuensi **900** dan **1800** MHz pada kontrol *segmented*, ubah lingkungan (`LOS` / `NLOS`), dan geser jarak (`1–12 km`).
4. Klik **Jalankan Monte Carlo** untuk menjalankan transmisi bit acak aktual dan membandingkan konstelasi I/Q nyata (**Dioptimalkan vs S0** maupun **Antar Frekuensi**).
5. (Opsional) Buka **Sensitivitas eksploratori** di panel kiri untuk menguji target BER `1e-3` atau suplemen `700 MHz` (eksploratori terinspirasi Reddy 2022, bukan replikasi Reddy, dan tidak mengubah `outputs/`).
6. Buka tab **B. Hasil penelitian (CSV & PNG)** untuk melihat grafik publikasi serta mengunduh file `.csv` maupun `.png`, dan tab **C. Metodologi & Batasan** untuk persamaan matematis.

---

## Tim dan Tanggung Jawab

Seluruh enam anggota Kelompok 1 berpartisipasi aktif dalam presentasi akhir.

| Nama | Tanggung Jawab |
|---|---|
| **Yusril** | Presentasi dan PPT |
| **Rizqul** | Presentasi dan PPT |
| **Baihaqy** | Analisis, diskusi, dan laporan |
| **Jeyd** | Analisis, diskusi, dan laporan |
| **Aditya** | Program dan simulasi |
| **Zahran** | Program dan simulasi |

**Kredit desain:** Tampilan antarmuka (*light workbench*, rail parameter kiri, *telemetry strip*, kurva SNR, konstelasi, dan zona radial) diadaptasi dari prototipe HTML/CSS/JS buatan **Zahran** ([prototypes/dashboard_rurallink.html](prototypes/dashboard_rurallink.html)), lalu diintegrasikan ke Streamlit ([app.py](app.py)) di atas mesin Python tervalidasi (`src/`).

---

## Pusat Sumber Daya Tim

### TIM PPT — Yusril & Rizqul
- [Ringkasan Penelitian (Bahasa Sederhana)](docs/RESEARCH_OVERVIEW.md)
- [Ringkasan Angka Terverifikasi (outputs/summary.md)](outputs/summary.md)
- [Panduan Demo Presentasi](docs/DEMO_GUIDE.md) dan [Panduan Presentasi & Q&A](docs/PRESENTATION_GUIDE.md)
- Grafik siap slide: [adaptive_coverage_radius.png](outputs/figures/adaptive_coverage_radius.png), [adaptive_rate_vs_distance.png](outputs/figures/adaptive_rate_vs_distance.png), [uplink_snr_vs_distance.png](outputs/figures/uplink_snr_vs_distance.png)
- Aplikasi live: [https://rural-link.streamlit.app/](https://rural-link.streamlit.app/)

### TIM ANALISIS — Baihaqy & Jeyd
- [Ringkasan Eksperimen (outputs/summary.md)](outputs/summary.md)
- Dataset CSV: [adaptive_coverage_summary.csv](outputs/results/adaptive_coverage_summary.csv), [adaptive_strategy_comparison.csv](outputs/results/adaptive_strategy_comparison.csv), [adaptive_coverage_curves.csv](outputs/results/adaptive_coverage_curves.csv), [adaptive_mc_validation.csv](outputs/results/adaptive_mc_validation.csv), [ber_validation.csv](outputs/results/ber_validation.csv), [link_budget_validation.csv](outputs/results/link_budget_validation.csv), [modulation_thresholds.csv](outputs/results/modulation_thresholds.csv)
- [Metodologi Matematis](docs/METHODOLOGY.md) dan [Keputusan Ilmiah (DECISIONS.md)](docs/DECISIONS.md)
- [Panduan Membaca Hasil & CI](docs/RESULTS_GUIDE.md) dan [Kamus Istilah](docs/GLOSSARY.md)
- [Daftar Referensi & DOI](docs/REFERENCES.md)

### TIM PROGRAM — Aditya & Zahran
- Kode sumber mesin: `src/` ([propagation.py](src/propagation.py), [link_budget.py](src/link_budget.py), [modulation.py](src/modulation.py), [channels.py](src/channels.py), [metrics.py](src/metrics.py), [adaptive.py](src/adaptive.py)), [config.py](config.py), [app.py](app.py)
- [Arsitektur Sistem](docs/ARCHITECTURE.md) dan [Panduan Developer](docs/DEVELOPER_GUIDE.md)
- Pengujian otomatis: `tests/` ([test_environment.py](tests/test_environment.py), [test_scientific_engine.py](tests/test_scientific_engine.py), [test_adaptive.py](tests/test_adaptive.py), [test_app.py](tests/test_app.py))
- Peluncur offline: [run_local.ps1](run_local.ps1)
- Prototipe awal Zahran: [prototypes/dashboard_rurallink.html](prototypes/dashboard_rurallink.html) dan [prototypes/README.md](prototypes/README.md)

---

## Dokumentasi Teknis

### Menjalankan Secara Lokal (Offline Fallback, Python 3.12)

```powershell
git clone https://github.com/Legorvey/rural-link.git
cd rural-link
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements-dev.txt
.\run_local.ps1
```

### Pengujian dan Linter

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
```

### Struktur Ringkas Repositori

```text
rural-link/
├── app.py                 # Antarmuka Streamlit terintegrasi (memanggil src/)
├── config.py              # Parameter default & batasan tervalidasi
├── run_local.ps1          # Peluncur offline menggunakan .venv
├── requirements.txt       # Dependensi runtime terpin (Streamlit Cloud)
├── src/                   # Mesin simulasi ilmiah & optimasi adaptif
├── experiments/           # Skrip eksperimen deterministik
├── tests/                 # 96 pengujian otomatis (pytest + AppTest)
├── outputs/               # summary.md, CSV hasil, dan grafik PNG
├── prototypes/            # Prototipe HTML awal Zahran (referensi visual)
└── docs/                  # Dokumentasi metode, demo, hasil, dan tim
```

**Info Deployment:** Streamlit Community Cloud memakai file utama `app.py`, Python `3.12` ([.python-version](.python-version)), dan [requirements.txt](requirements.txt). Detail lanjutan tersedia di [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) dan [docs/PROGRESS.md](docs/PROGRESS.md).

---

## Referensi dan Batasan

### Referensi Utama
- **Park et al. (2023)** — *Close-In (CI) Path Loss* pedesaan LOS/NLOS (1400 MHz), DOI: `10.1109/ACCESS.2023.3293496` (lihat [docs/REFERENCES.md](docs/REFERENCES.md)).
- **Cho & Yoon (2002)** — Rumus BER QAM Gray-coded eksak, *IEEE Trans. Commun.*, DOI: `10.1109/TCOMM.2002.1006557`.
- **Reddy (2022)** & **Yogapratama (2015)** — Parameter RF uplink seluler pedesaan (rincian verifikasi di [docs/REFERENCES.md](docs/REFERENCES.md)).

### Batasan Model
- Simulator ini adalah **model *link-level* yang disederhanakan**, bukan implementasi penuh protokol LTE/5G-NR, tanpa *channel coding* (FEC), tanpa interferensi antar-sel, dan tanpa penjadwalan multi-pengguna.
- Parameter propagasi CI diekstrapolasi dari kampanye pengukuran 1400 MHz dan belum dikalibrasi dengan pengukuran lapangan di wilayah 3T Indonesia.
- Visualisasi zona cakupan adalah model radial hipotetis tanpa kontur medan, dan tidak boleh ditafsirkan sebagai prediksi cakupan geografis lapangan.
