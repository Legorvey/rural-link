"""Structured Indonesian research encyclopedia and glossary data for RuralLink.

Single source of truth shared between Tab D (Ensiklopedia RuralLink) in app.py
and docs/GLOSSARY.md. No scientific engine calculations are performed here.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

CATEGORIES: tuple[str, ...] = (
    "A. Fundamental Seluler & Telekomunikasi",
    "B. Propagasi Radio",
    "C. Link Budget & Daya",
    "D. Model Kanal & Penerimaan",
    "E. Modulasi Digital",
    "F. Kinerja & Keandalan",
    "G. Optimasi & Skenario",
    "H. Simulasi & Statistik",
    "I. Literatur Riset",
    "J. Perangkat Lunak & Artefak Riset",
)


@dataclass(frozen=True)
class GlossaryEntry:
    """Single encyclopedia entry with 4 display columns and category metadata."""

    kategori: str
    istilah: str
    kepanjangan: str
    penjelasan: str
    persamaan: str


ENTRIES: tuple[GlossaryEntry, ...] = (
    # ================================================================== A
    GlossaryEntry(
        CATEGORIES[0],
        "Telecommunications",
        "Telekomunikasi",
        (
            "[Latar belakang teoretis] Pertukaran informasi jarak jauh melalui sinyal listrik, "
            "optik, atau gelombang radio; menjadi payung sistem komunikasi nirkabel RuralLink."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Digital communication",
        "Komunikasi Digital",
        (
            "[Diimplementasikan di RuralLink] Transmisi informasi dalam bentuk bit biner yang "
            "dipetakan ke simbol modulasi diskret; memungkinan deteksi berbasis probabilitas "
            "kesalahan bit (BER)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Rural connectivity",
        "Konektivitas Pedesaan",
        (
            "[Konteks literatur / tidak diimplementasikan] Penyediaan layanan seluler di wilayah "
            "berpenduduk jarang dengan sel berjari-jari besar (km), di mana cakupan lebih "
            "menentukan daripada kapasitas padat."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "3T",
        "Tertinggal, Terdepan, Terluar",
        (
            "[Konteks literatur / tidak diimplementasikan] Klasifikasi wilayah prioritas "
            "pembangunan Indonesia (Komdigi 2025: 6.747 lokasi BTS di 3T) yang memotivasi studi "
            "perluasan jangkauan uplink RuralLink."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "BTS / BS / eNB",
        "Base Transceiver Station / Base Station / Evolved NodeB",
        (
            "[Diimplementasikan di RuralLink] Menara pemancar-penerima tetap yang menerima sinyal "
            "uplink dari UE; dimodelkan dengan penguatan antena Gr = 11 dBi, rugi feeder 5 dB, dan "
            "NF = 4 dB."
        ),
        "Gr = 11 dBi, L_feeder = 5 dB, NF = 4 dB",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "UE",
        "User Equipment",
        (
            "[Diimplementasikan di RuralLink] Perangkat pengguna (ponsel/modem) dengan daya pancar "
            "terbatas maks 23 dBm (200 mW) dan antena 0 dBi, sehingga menjadi titik lemah tautan "
            "uplink."
        ),
        "Pt_maks = 23 dBm (200 mW), Gt = 0 dBi",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Uplink / Downlink",
        "Tautan Naik (UE ke BTS) / Tautan Turun (BTS ke UE)",
        (
            "[Diimplementasikan di RuralLink] RuralLink memodelkan Uplink karena daya UE (23 dBm) "
            "jauh lebih kecil daripada BTS (~43-46 dBm pada downlink), sehingga jangkauan sel "
            "dibatasi oleh uplink."
        ),
        "Uplink: UE -> BTS",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "LTE / 4G / 5G / NR",
        "Long Term Evolution / 4th Gen / 5th Gen / New Radio",
        (
            "[Konteks literatur / tidak diimplementasikan] Standar seluler 3GPP; RuralLink "
            "meminjam"
            "parameter fisik PRB 180 kHz dan daya UE 23 dBm dari LTE/NR, namun tidak "
            "mengimplementasikan stack protokol LTE/NR penuh."
        ),
        "B_RB = 180 kHz",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "RAN",
        "Radio Access Network",
        (
            "[Latar belakang teoretis] Bagian jaringan seluler yang menghubungkan UE dengan BTS "
            "melalui antarmuka radio; RuralLink hanya mensimulasikan tautan fisik single-user di "
            "dalam RAN."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Cell / Cell radius / Cell edge",
        "Sel / Radius Sel / Tepi Sel",
        (
            "[Diimplementasikan di RuralLink] Wilayah cakupan satu BTS; RuralLink mengevaluasi "
            "jarak 1-12 km dan mendemonstrasikan pemulihan tepi sel (mis. 5 km pada 900 MHz NLOS) "
            "lewat S3 dibanding S0."
        ),
        "d in [1.0, 12.0] km",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Macrocell / RMa / LMLC",
        "Sel Makro / Rural Macro / Low Mobility Large Cell",
        (
            "[Konteks literatur / tidak diimplementasikan] Skenario sel pedesaan beradius besar "
            "(hingga puluhan km) pada Reddy (2022) untuk 700 MHz; menginspirasi evaluasi suplemen "
            "700 MHz di RuralLink."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "ISD",
        "Inter-Site Distance",
        (
            "[Konteks literatur / tidak diimplementasikan] Jarak antar-BTS berdekatan dalam "
            "perencanaan jaringan multi-sel; tidak dimodelkan di RuralLink karena simulasi "
            "bersifat"
            "single-cell tanpa interferensi."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Carrier frequency",
        "Frekuensi Pembawa (fc)",
        (
            "[Diimplementasikan di RuralLink] Frekuensi tengah gelombang radio; frekuensi lebih "
            "rendah menghasilkan FSPL lebih kecil (+6,02 dB keunggulan jangkauan 900 MHz dibanding "
            "1800 MHz)."
        ),
        "fc in {900, 1800} MHz (primer); 700 MHz (suplemen)",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Frequency band",
        "Pita Frekuensi",
        (
            "[Diimplementasikan di RuralLink] Rentang spektrum berizin untuk operasi seluler; "
            "berbeda dari model kanal (AWGN/Rayleigh) karena pita menentukan redaman propagasi, "
            "bukan statistik fading sesaat."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "700 / 900 / 1800 MHz",
        "Pita Spektrum Evaluasi RuralLink",
        (
            "[Diimplementasikan di RuralLink] 900 dan 1800 MHz adalah konfigurasi riset utama "
            "Indonesia 3T; 700 MHz adalah suplemen sensitivitas (terinspirasi Reddy 2022 di atas "
            "model CI Park 2023, bukan replikasi Reddy)."
        ),
        "Delta PL(1800 vs 900) = 20 log10(2) = 6,02 dB",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Channel bandwidth",
        "Lebar Pita Kanal Nominal (B_ch)",
        (
            "[Diimplementasikan di RuralLink] Total lebar pita kanal LTE acuan sebesar 5 MHz "
            "(Yogapratama Table IV) yang memuat hingga 25 RB aktif (4,5 MHz)."
        ),
        "B_ch = 5,0 MHz",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Active bandwidth",
        "Lebar Pita Aktif (B_active)",
        (
            "[Diimplementasikan di RuralLink] Porsi spektrum yang benar-benar dialokasikan kepada "
            "UE; mempersempit B_active menurunkan noise floor penerima sekaligus mengurangi laju "
            "data nominal."
        ),
        "B_active = N_RB x 180 kHz (maks 4,5 MHz)",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "RB / PRB",
        "Resource Block / Physical Resource Block",
        (
            "[Diimplementasikan di RuralLink] Satuan alokasi frekuensi minimum selebar 180 kHz "
            "(N_RB in {1, 2, 5, 10, 25}). Berbeda dari Rb (bit rate): RB adalah satuan "
            "spektrum, Rb"
            "adalah laju bit."
        ),
        "B_RB = 180.000 Hz; N_RB in {1, 2, 5, 10, 25}",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Subcarrier",
        "Sub-pembawa",
        (
            "[Konteks literatur / tidak diimplementasikan] Pembawa ortogonal sempit selebar 15 kHz "
            "di dalam RB LTE (12 subcarrier x 15 kHz = 180 kHz); tidak disimulasikan "
            "per-subcarrier"
            "di RuralLink."
        ),
        "12 x 15 kHz = 180 kHz",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "OFDM / OFDMA / SC-FDMA",
        "Orthogonal Frequency-Division Multiplexing / Multiple Access / Single-Carrier FDMA",
        (
            "[Konteks literatur / tidak diimplementasikan] Teknik transmisi multi-pembawa LTE "
            "(SC-FDMA di uplink untuk PAPR rendah); RuralLink mengabstraksikannya menjadi "
            "blok pita"
            "aktif ekivalen."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "MIMO",
        "Multiple-Input Multiple-Output",
        (
            "[Konteks literatur / tidak diimplementasikan] Teknik multi-antena (mis. 16-antena BS "
            "pada Reddy 2022) untuk penguatan diversity/array; TIDAK diimplementasikan di "
            "RuralLink"
            "(model antena tunggal SISO)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[0],
        "Coverage / Capacity",
        "Cakupan / Kapasitas",
        (
            "[Diimplementasikan di RuralLink] Pertukaran mendasar jaringan seluler: memperluas "
            "jarak jangkauan (coverage) dilakukan dengan menurunkan order modulasi dan N_RB, yang "
            "menurunkan laju (capacity)."
        ),
        "-",
    ),
    # ================================================================== B
    GlossaryEntry(
        CATEGORIES[1],
        "RF",
        "Radio Frequency",
        (
            "[Diimplementasikan di RuralLink] Sinyal elektromagnetik berfrekuensi tinggi yang "
            "membawa informasi dari UE ke BTS melalui kanal radio."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "LOS / NLOS",
        "Line-of-Sight / Non-Line-of-Sight",
        (
            "[Diimplementasikan di RuralLink] LOS berarti jalur pandang langsung tanpa halangan; "
            "NLOS berarti jalur terhalang vegetasi/medan dengan eksponen path loss dan deviasi "
            "shadowing jauh lebih besar."
        ),
        "LOS: n=2,16, sigma=3,07 dB; NLOS: n=2,56, sigma=11,40 dB",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Path loss / PL",
        "Rugi-rugi Lintasan",
        (
            "[Diimplementasikan di RuralLink] Redaman total daya sinyal antara antena pemancar dan "
            "penerima dalam skala dB; bertambah terhadap jarak dan frekuensi."
        ),
        "PL = FSPL(1m, f) + 10 n log10(d_m) + X_sigma [dB]",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "FSPL",
        "Free-Space Path Loss",
        (
            "[Diimplementasikan di RuralLink] Redaman ruang bebas pada jarak referensi d0 = 1 m "
            "sebagai suku jangkar model CI."
        ),
        "FSPL(1m, f_GHz) = 32,4 + 20 log10(f_GHz) [dB]",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Friis equation",
        "Persamaan Transmisi Friis",
        (
            "[Latar belakang teoretis] Rumus dasar daya terima di ruang bebas tanpa halangan yang "
            "melandasi suku 20 log10(4 pi d / lambda) pada FSPL."
        ),
        "Pr / Pt = Gt Gr (lambda / (4 pi d))^2",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "CI / Close-In",
        "Close-In Free-Space Reference Path Loss Model",
        (
            "[Diimplementasikan di RuralLink] Model path loss fisik satu parameter (n) yang "
            "berjangkar pada FSPL di d0 = 1 m; memakai parameter Park (2023) 1400 MHz "
            "diekstrapolasi ke 700/900/1800 MHz."
        ),
        "PL(f_GHz, d_m) = 32,4 + 20 log10(f_GHz) + 10 n log10(d_m) + X_sigma",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "SPM",
        "Standard Propagation Model",
        (
            "[Konteks literatur / tidak diimplementasikan] Model empiris Hata-terkalibrasi yang "
            "dipakai Khan (2025) untuk downlink 2 GHz; TIDAK diimplementasikan di RuralLink "
            "(RuralLink memakai model CI)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "PLE / n",
        "Path Loss Exponent",
        (
            "[Diimplementasikan di RuralLink] Eksponen peluruhan daya terhadap jarak pada model CI "
            "(ruang bebas n = 2); nilai RuralLink dari Park (2023) Table II."
        ),
        "n_LOS = 2,16; n_NLOS = 2,56",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "d0",
        "Reference Distance",
        (
            "[Diimplementasikan di RuralLink] Jarak referensi dekat sebesar 1 meter tempat FSPL "
            "dievaluasi pada model Close-In."
        ),
        "d0 = 1 m",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Shadowing / Log-normal shadow fading",
        "Redaman Bayangan Log-Normal (X_sigma)",
        (
            "[Diimplementasikan di RuralLink] Fluktuasi skala besar daya rata-rata akibat "
            "bukit/pepohonan; dimodelkan terdistribusi Normal dalam dB dengan rata-rata 0 dan "
            "simpangan baku sigma."
        ),
        "X_sigma ~ N(0, sigma^2) [dB]",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Standard deviation / sigma",
        "Simpangan Baku Shadowing",
        (
            "[Diimplementasikan di RuralLink] Ukuran sebaran redaman bayangan dalam dB; NLOS "
            "memiliki sigma jauh lebih besar (11,40 dB) daripada LOS (3,07 dB)."
        ),
        "sigma_LOS = 3,07 dB; sigma_NLOS = 11,40 dB",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Median path loss",
        "Path Loss Median",
        (
            "[Diimplementasikan di RuralLink] Nilai path loss deterministik ketika X_sigma = 0 dB "
            "(persentil ke-50). Bersifat deterministik dan bukan ukuran keandalan 95%."
        ),
        "PL_median = PL(X_sigma = 0) [dB]",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "95% shadow margin",
        "Margin Shadowing 95%",
        (
            "[Diimplementasikan di RuralLink] Cadangan redaman analitis 1,645 * sigma agar "
            "probabilitas shadowing melampaui margin <= 5%. Tidak otomatis sama dengan keandalan "
            "kanal gabungan (+Rayleigh) dan tidak dihitung ganda di atas X_sigma acak."
        ),
        "M_SF,95% = 1,645 x sigma [dB] (NLOS = 18,75 dB)",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Multipath",
        "Lintasan Jamak",
        (
            "[Latar belakang teoretis] Fenomena sinyal tiba di BTS melalui banyak lintasan "
            "pantul/hambur dengan fase berbeda sehingga menimbulkan interferensi konstruktif dan "
            "destruktif (fading cepat)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Reflection / diffraction / scattering",
        "Pemantulan / Difraksi / Penghamburan",
        (
            "[Konteks literatur / tidak diimplementasikan] Mekanisme fisik propagasi gelombang "
            "radio; efek agregatnya tercermin dalam eksponen n dan fading Rayleigh, bukan simulasi "
            "ray-tracing/geometri."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Delta-Bullington / Knife-edge diffraction",
        "Difraksi Delta-Bullington / Tepi Tajam",
        (
            "[Konteks literatur / tidak diimplementasikan] Metode perhitungan rugi difraksi medan "
            "(ITU-R P.526) pada Park (2023) Eq. (4); TIDAK diimplementasikan karena profil elevasi "
            "medan tidak tersedia (Keputusan D11)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Large-scale fading",
        "Fading Skala Besar",
        (
            "[Diimplementasikan di RuralLink] Perubahan daya sinyal rata-rata terhadap jarak "
            "ratusan meter akibat path loss CI dan shadowing log-normal X_sigma."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[1],
        "Small-scale fading",
        "Fading Skala Kecil",
        (
            "[Diimplementasikan di RuralLink] Variasi cepat amplitudo/fase sinyal pada skala "
            "setengah panjang gelombang akibat multipath; dimodelkan sebagai koefisien kanal "
            "Rayleigh h."
        ),
        "-",
    ),
    # ================================================================== C
    GlossaryEntry(
        CATEGORIES[2],
        "Link budget",
        "Anggaran Tautan",
        (
            "[Diimplementasikan di RuralLink] Pembukuan seluruh penguatan dan rugi-rugi dari "
            "pemancar UE hingga penerima BTS untuk menghitung daya terima Pr, derau N, dan SNR."
        ),
        "SNR_dB = Pr_dBm - N_dBm",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Pt / Pr",
        "Transmit Power / Received Power",
        (
            "[Diimplementasikan di RuralLink] Daya pancar total UE (maks 23 dBm) dan daya sinyal "
            "yang diterima di masukan penerima BTS setelah melewati penguatan antena dan rugi "
            "lintasan/kabel."
        ),
        "Pr = Pt + Gt + Gr - PL - L_feeder - L_body [dBm]",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Gt / Gr / Antenna gain",
        "Penguatan Antena Pemancar / Penerima",
        (
            "[Diimplementasikan di RuralLink] Kemampuan antena memfokuskan daya ke arah tertentu "
            "relatif terhadap radiator isotropis (dBi); UE 0 dBi, BTS 11 dBi."
        ),
        "Gt = 0 dBi, Gr = 11 dBi",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Feeder loss / Body loss",
        "Rugi Kabel Feeder / Rugi Tubuh Pengguna",
        (
            "[Diimplementasikan di RuralLink] Redaman tetap pada kabel antena BTS (5 dB) dan "
            "serapan tubuh pengguna di dekat UE (3 dB) dari Yogapratama Table IV."
        ),
        "L_feeder = 5,0 dB; L_body = 3,0 dB",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "dB / dBm / dBi",
        "Desibel / Desibel-miliwatt / Desibel-isotropis",
        (
            "[Diimplementasikan di RuralLink] Penting dibedakan: dB adalah rasio tak berdimensi "
            "(rugi/SNR); dBm adalah daya absolut relatif terhadap 1 mW; dBi adalah "
            "penguatan antena"
            "relatif terhadap antena isotropis."
        ),
        "P_dBm = 10 log10(P_mW)",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Watt / milliwatt",
        "Satuan Daya SI (W / mW)",
        (
            "[Diimplementasikan di RuralLink] 23 dBm setara dengan 200 mW (0,2 W), jauh di bawah "
            "daya BTS makro puluhan Watt."
        ),
        "10^(23/10) mW = 199,53 mW (~0,2 W)",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Hz / kHz / MHz / GHz",
        "Hertz / Kilohertz / Megahertz / Gigahertz",
        (
            "[Diimplementasikan di RuralLink] Satuan frekuensi dan lebar pita: 1 RB = 180 kHz, "
            "kanal = 5 MHz, pembawa = 700/900/1800 MHz (0,7/0,9/1,8 GHz pada rumus FSPL)."
        ),
        "1 GHz = 1000 MHz = 10^6 kHz = 10^9 Hz",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Thermal noise / N0 / kTB",
        "Derau Termal / Rapat Daya Derau",
        (
            "[Diimplementasikan di RuralLink] Derau acak elektron pada suhu referensi T0 = 290 K "
            "dengan rapat daya -174 dBm/Hz, bertambah sebanding dengan lebar pita aktif B_active."
        ),
        "N0_th = k_B T0 = -174 dBm/Hz",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Noise floor",
        "Lantai Derau Penerima (N_dBm)",
        (
            "[Diimplementasikan di RuralLink] Daya derau total di dalam pita aktif termasuk Noise "
            "Figure; berkurang ketika N_RB dikurangi (pada 1 RB = -117,45 dBm)."
        ),
        "N_dBm = -174 + 10 log10(B_active) + NF",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "NF",
        "Noise Figure",
        (
            "[Diimplementasikan di RuralLink] Tambahan derau oleh rangkaian RF penerima BTS "
            "di atas"
            "batas termal ideal; nilai default 4,0 dB."
        ),
        "NF = 4,0 dB",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "SNR / SINR",
        "Signal-to-Noise Ratio / Signal-to-Interference-plus-Noise Ratio",
        (
            "[Diimplementasikan di RuralLink] RuralLink menghitung SNR (noise-limited, tanpa "
            "interferensi antar-sel); SINR berlaku bila interferensi dimodelkan."
        ),
        "SNR_dB = Pr_dBm - N_dBm",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Es / Eb",
        "Energi per Simbol / Energi per Bit",
        (
            "[Diimplementasikan di RuralLink] Energi rata-rata satu simbol modulasi (dinormalisasi "
            "Es = 1) dan energi per bit informasi Eb = Es / k."
        ),
        "Es = 1; Eb = Es / log2(M)",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Es/N0 / Eb/N0",
        "Rasio Energi Simbol/Bit terhadap Rapat Derau",
        (
            "[Diimplementasikan di RuralLink] Wajib dibedakan: dengan Rs = B_active, Es/N0 = "
            "SNR_linear, sedangkan Eb/N0 = (Es/N0)/k lebih rendah sebesar 10 log10(k) dB untuk "
            "modulasi berorder tinggi."
        ),
        "(Eb/N0)_dB = SNR_dB - 10 log10(log2 M)",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Power per RB / Power concentration",
        "Daya per RB / Pemusatan Daya",
        (
            "[Diimplementasikan di RuralLink] Dengan daya total UE tetap 23 dBm, memperkecil N_RB "
            "memusatkan daya pada lebih sedikit RB dan mempersempit noise floor, menaikkan SNR "
            "hingga +13,98 dB (25->1 RB) tanpa dihitung ganda."
        ),
        "P_RB = Pt - 10 log10(N_RB); Delta SNR = 10 log10(25 / N_RB)",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Power-limited uplink",
        "Uplink Terbatas Daya",
        (
            "[Diimplementasikan di RuralLink] Rezim operasi ketika daya pancar UE dibatasi 23 dBm "
            "sehingga jangkauan sel dibatasi oleh anggaran daya uplink, bukan oleh lebar spektrum."
        ),
        "Pt <= 23 dBm (hard-capped)",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Receiver sensitivity",
        "Sensitivitas Penerima",
        (
            "[Latar belakang teoretis] Daya terima minimum agar target BER tercapai; di RuralLink "
            "ekuivalen dengan N_dBm + ambang Es/N0 modulasi aktif."
        ),
        "S_rx = N_dBm + (Es/N0)_thr [dBm]",
    ),
    GlossaryEntry(
        CATEGORIES[2],
        "Interference",
        "Interferensi Kanal",
        (
            "[Konteks literatur / tidak diimplementasikan] Sinyal pengganggu dari "
            "sel/pengguna lain"
            "(co-channel/adjacent); TIDAK dimodelkan di RuralLink (asumsi single-user "
            "noise-limited)."
        ),
        "-",
    ),
    # ================================================================== D
    GlossaryEntry(
        CATEGORIES[3],
        "AWGN / Gaussian noise",
        "Additive White Gaussian Noise",
        (
            "[Diimplementasikan di RuralLink] Model kanal dasar tanpa fading dengan derau kompleks "
            "i.i.d. varians N0/2 per dimensi I dan Q; dipakai untuk menurunkan ambang "
            "switching dan"
            "validasi MC."
        ),
        "y = x + w, w ~ CN(0, N0), N0 = 1 / (Es/N0)",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "Rayleigh fading",
        "Fading Rayleigh",
        (
            "[Diimplementasikan di RuralLink] Model multipath NLOS tanpa komponen dominan, dengan "
            "amplitudo |h| berdistribusi Rayleigh dan E[|h|^2] = 1; menurunkan keandalan bila "
            "terjadi deep fade."
        ),
        "y = h x + w, h = (h_I + j h_Q)/sqrt(2), E[|h|^2] = 1",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "Rician fading / Rician K-factor",
        "Fading Rician / Faktor-K Rician",
        (
            "[Konteks literatur / tidak diimplementasikan] Model fading yang memiliki satu "
            "komponen"
            "LOS dominan selain multipath (K = rasio daya LOS terhadap tersebar); TIDAK "
            "diimplementasikan di RuralLink."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "Flat fading",
        "Fading Datar (Tidak Selektif Frekuensi)",
        (
            "[Diimplementasikan di RuralLink] Seluruh pita aktif mengalami satu koefisien kanal "
            "skalar h tanpa dispersi antarsimbol (ISI)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "Block fading / Independent fading",
        "Fading Blok / Fading Independen",
        (
            "[Diimplementasikan di RuralLink] Independent fading (block_size=1) mengacak h setiap "
            "simbol; block fading menahan h konstan selama satu blok simbol (dalam mode ini CI bit "
            "independen tidak berlaku)."
        ),
        "block_size = 1 (default MC)",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "CSI / Perfect CSI / Instantaneous CSI",
        "Channel State Information (Sempurna / Sesaat)",
        (
            "[Diimplementasikan di RuralLink] Pengetahuan penerima atas koefisien kanal h. Pada "
            "mode Rayleigh adaptif, scheduler memakai CSI sesaat (h diketahui sempurna per "
            "realisasi) untuk memilih modulasi-RB."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "Instantaneous SNR / Average SNR",
        "SNR Sesaat / SNR Rata-rata",
        (
            "[Diimplementasikan di RuralLink] SNR rata-rata ditentukan oleh path loss + shadowing; "
            "SNR sesaat setelah Rayleigh adalah gamma_inst = gamma_avg * |h|^2."
        ),
        "gamma_inst = gamma_avg |h|^2",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "Complex channel coefficient h",
        "Koefisien Kanal Kompleks h",
        (
            "[Diimplementasikan di RuralLink] Pengali acak kompleks sirkuler-simetris berenergi "
            "rata-rata 1 yang merepresentasikan redaman dan pergeseran fase kanal Rayleigh."
        ),
        "h ~ CN(0, 1)",
    ),
    GlossaryEntry(
        CATEGORIES[3],
        "Coherent detection / Equalization / Zero-forcing",
        "Deteksi Koheren / Ekualisasi Zero-Forcing (ZF)",
        (
            "[Diimplementasikan di RuralLink] Penerima membagi sinyal terima dengan estimasi "
            "sempurna h (x_hat = y / h) untuk memulihkan fase dan amplitudo sebelum pemetaan ulang "
            "simbol."
        ),
        "x_hat = y / h = x + w / h",
    ),
    # ================================================================== E
    GlossaryEntry(
        CATEGORIES[4],
        "Bit / Symbol",
        "Bit Informasi / Simbol Modulasi",
        (
            "[Diimplementasikan di RuralLink] Bit adalah unit biner {0,1}; satu simbol membawa k = "
            "log2(M) bit sekaligus pada bidang kompleks I/Q."
        ),
        "k = log2(M) bit/simbol",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Bit rate (Rb) / Symbol rate (Rs) / Baud",
        "Laju Bit / Laju Simbol (Baud)",
        (
            "[Diimplementasikan di RuralLink] Rs = B_active (simbol/detik = baud) di bawah asumsi "
            "ideal tanpa pulse-shaping excess bandwidth; Rb = Rs * k = B_active * log2(M). Jangan "
            "tertukar dengan RB (Resource Block)."
        ),
        "Rs = B_active; Rb = B_active x k [bps]",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Modulation / Demodulation",
        "Modulasi / Demodulasi",
        (
            "[Diimplementasikan di RuralLink] Pemetaan bit ke titik konstelasi kompleks (modulasi) "
            "dan pemulihan bit dari simbol terekualisasi di penerima (demodulasi)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "PSK / QAM",
        "Phase-Shift Keying / Quadrature Amplitude Modulation",
        (
            "[Diimplementasikan di RuralLink] PSK mengkodekan bit pada fase (BPSK, QPSK); QAM "
            "mengkodekan bit pada amplitudo dan fase sekaligus (16-QAM, 64-QAM) untuk efisiensi "
            "spektral lebih tinggi."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "BPSK / QPSK / 16-QAM / 64-QAM",
        "Skema Modulasi RuralLink",
        (
            "[Diimplementasikan di RuralLink] Empat konstelasi tervalidasi: BPSK (M=2, k=1), QPSK "
            "(M=4, k=2), 16-QAM (M=16, k=4), 64-QAM (M=64, k=6). Semakin tinggi M, semakin besar "
            "laju namun butuh SNR lebih tinggi."
        ),
        "M in {2, 4, 16, 64}, k in {1, 2, 4, 6}",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Modulation order M / Bits per symbol k",
        "Orde Modulasi M / Bit per Simbol k",
        (
            "[Diimplementasikan di RuralLink] Jumlah titik konstelasi M = 2^k; pada simulasi Monte "
            "Carlo, panjang bit diselaraskan ke kelipatan k agar tanpa padding semu."
        ),
        "M = 2^k",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Gray coding",
        "Pengkodean Gray",
        (
            "[Diimplementasikan di RuralLink] Pelabelan bit sehingga dua simbol bertetangga di "
            "konstelasi hanya berbeda tepat 1 bit; menurunkan BER secara signifikan "
            "dibanding biner"
            "alami (lihat Keputusan D10/D13)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "I/Q / Complex baseband",
        "In-phase & Quadrature / Baseband Kompleks",
        (
            "[Diimplementasikan di RuralLink] Representasi sinyal dua dimensi (komponen riil I dan "
            "imajiner Q) yang ekivalen dengan gelombang pembawa kosinus dan sinus."
        ),
        "x = x_I + j x_Q",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Constellation diagram / Normalization",
        "Diagram Konstelasi / Normalisasi Energi (Es = 1)",
        (
            "[Diimplementasikan di RuralLink] Plot sebaran simbol I/Q. Seluruh konstelasi "
            "dinormalisasi sehingga rata-rata energi per simbol E[|x|^2] = 1 (faktor 1, 1/sqrt(2), "
            "1/sqrt(10), 1/sqrt(42))."
        ),
        "E[|x|^2] = 1",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Decision boundary / Maximum likelihood detection",
        "Batas Keputusan / Deteksi ML",
        (
            "[Diimplementasikan di RuralLink] Pada derau Gaussian putih dengan probabilitas simbol "
            "seragam, detektor ML memilih titik konstelasi terdekat (pemotongan PAM 1D pada "
            "sumbu I"
            "dan Q)."
        ),
        "s_hat = argmin_s |x_hat - s|^2",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Adaptive modulation / AMC / MCS",
        "Modulasi Adaptif / Adaptive Modulation & Coding / Modulation & Coding Scheme",
        (
            "[Diimplementasikan di RuralLink] Penyesuaian modulasi (dan RB) mengikuti kondisi "
            "kanal; RuralLink mengimplementasikan adaptasi uncoded (tanpa coding rate MCS LTE)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Channel coding / Coding rate",
        "Pengkodean Kanal (FEC) / Laju Kode",
        (
            "[Konteks literatur / tidak diimplementasikan] Penambahan bit redundansi (Turbo/LDPC) "
            "untuk koreksi galat; TIDAK diimplementasikan di RuralLink sehingga seluruh laju dan "
            "ambang bersifat uncoded."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Spectral efficiency",
        "Efisiensi Spektral (eta)",
        (
            "[Diimplementasikan di RuralLink] Bit per detik per Hz; diukur terhadap pita aktif "
            "(eta_active = k) maupun kanal nominal 5 MHz (eta_channel = Rb / 5 MHz)."
        ),
        "eta_active = k bps/Hz; eta_ch = Rb / 5e6 bps/Hz",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Nominal data rate / Effective nominal rate",
        "Laju Data Nominal / Laju Efektif Nominal",
        (
            "[Diimplementasikan di RuralLink] Laju uncoded B_active * k; bukan throughput LTE "
            "aktual. Laju efektif pada simulasi stokastik menghitung realisasi outage sebagai 0 "
            "bps."
        ),
        "Rb = B_active x k; R_eff = E[Rb | layak] x (1 - P_out)",
    ),
    GlossaryEntry(
        CATEGORIES[4],
        "Shannon capacity",
        "Kapasitas Shannon",
        (
            "[Diimplementasikan di RuralLink] Batas teoretis atas transmisi bebas galat pada kanal "
            "AWGN; ditampilkan hanya sebagai acuan di link_budget.py, bukan laju modulasi."
        ),
        "C = B_active log2(1 + SNR_linear) [bps]",
    ),
    # ================================================================== F
    GlossaryEntry(
        CATEGORIES[5],
        "BER",
        "Bit Error Rate",
        (
            "[Diimplementasikan di RuralLink] Rasio jumlah bit salah terhadap total bit terkirim; "
            "berbeda dari SER karena satu simbol salah pada M-QAM (Gray-coded) umumnya hanya "
            "merusak ~1 dari k bit."
        ),
        "BER = N_bit_err / N_bits",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "SER",
        "Symbol Error Rate",
        (
            "[Diimplementasikan di RuralLink] Rasio simbol yang salah diputuskan; tidak boleh "
            "disamakan dengan BER (Keputusan D10 mengoreksi Khan 2025 yang menghilangkan faktor "
            "1/k)."
        ),
        "SER = N_sym_err / N_symbols",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "BER target 10^-2 / 10^-3",
        "Target BER Primer (1e-2) & Suplemen (1e-3)",
        (
            "[Diimplementasikan di RuralLink] 10^-2 adalah target BER riset utama (dari Khan 2025 "
            "Table 9); 10^-3 adalah kontrol suplemen sensitivitas yang menghitung ulang ambang "
            "Eb/N0 via brentq."
        ),
        "BER_target in {1e-2, 1e-3}",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Error count",
        "Jumlah Galat Bit",
        (
            "[Diimplementasikan di RuralLink] Cacah absolut bit berbeda antara transmisi dan "
            "demodulasi dalam simulasi Monte Carlo; menentukan lebar interval kepercayaan Wilson "
            "atau rule-of-three."
        ),
        "n_bit_errors in [0, n_bits]",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Switching threshold",
        "Ambang Perpindahan Modulasi",
        (
            "[Diimplementasikan di RuralLink] Nilai Eb/N0 minimum agar BER AWGN eksak (Cho & Yoon "
            "2002) <= BER_target; pada BER 1e-2: BPSK/QPSK 4,32 dB, 16-QAM 7,88 dB, 64-QAM 11,95 "
            "dB."
        ),
        "Es/N0_thr = Eb/N0_thr + 10 log10(k)",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Conditional BER / Average BER",
        "BER Bersyarat / BER Rata-rata",
        (
            "[Diimplementasikan di RuralLink] Wajib dibedakan: adaptasi Rayleigh CSI sesaat "
            "memilih"
            "opsi dari SNR sesaat sehingga BER bersyarat adalah BER AWGN (maks 1e-2); BER "
            "rata-rata"
            "Rayleigh (4-7%) berlaku bila tidak ada CSI sesaat."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Outage / Outage probability",
        "Kegagalan Tautan / Probabilitas Outage (P_out)",
        (
            "[Diimplementasikan di RuralLink] Kondisi ketika tidak ada kandidat (modulasi, N_RB) "
            "yang memenuhi ambang Eb/N0 pada suatu realisasi kanal."
        ),
        "P_out = N_outage / N_draws",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Reliability / 5% outage target / 95% reliability",
        "Keandalan 95% (Target Outage <= 5%)",
        (
            "[Diimplementasikan di RuralLink] Kriteria keandalan stokastik: tautan "
            "dinyatakan andal"
            "pada jarak d bila probabilitas outage <= 5% di bawah 5000 realisasi acak bersama."
        ),
        "P_out <= 0,05 (keandalan >= 95%)",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Reliable coverage radius",
        "Radius Cakupan Andal",
        (
            "[Diimplementasikan di RuralLink] Jarak terjauh pada grid 1-12 km di mana P_out tetap "
            "<= 5%; lebih ketat dan realistis dibanding radius cakupan median deterministik."
        ),
        "max {d : P_out(d) <= 0,05}",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Deterministic vs Stochastic coverage",
        "Cakupan Deterministik vs Stokastik",
        (
            "[Diimplementasikan di RuralLink] Cakupan deterministik memakai PL median "
            "(X_sigma = 0)"
            "dan bukan ukuran keandalan; cakupan stokastik memakai realisasi acak shadowing & "
            "Rayleigh."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Throughput / Goodput / QoS",
        "Throughput / Goodput / Quality of Service",
        (
            "[Konteks literatur / tidak diimplementasikan] Throughput/goodput LTE nyata "
            "memperhitungkan MAC, HARQ, dan overhead kontrol; RuralLink hanya melaporkan laju "
            "nominal uncoded dan outage."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[5],
        "Left/right censored radius (<1 km, >=12 km)",
        "Radius Tersensor Kiri / Kanan",
        (
            "[Diimplementasikan di RuralLink] Grid evaluasi dibatasi 1-12 km: '<1 km' berarti "
            "bahkan di 1 km sudah gagal; '>=12 km' berarti masih memenuhi syarat di batas atas 12 "
            "km."
        ),
        "d_grid in [1,00; 12,00] km (step 0,25 km)",
    ),
    # ================================================================== G
    GlossaryEntry(
        CATEGORIES[6],
        "Optimization / Objective function / Constraint",
        "Optimasi / Fungsi Objektif / Kendala",
        (
            "[Diimplementasikan di RuralLink] Memilih pasangan (modulasi, N_RB) yang memaksimalkan "
            "laju nominal Rb = B_active * k dengan kendala Eb/N0 >= Eb/N0_thr(BER_target) "
            "dan Pt <="
            "23 dBm."
        ),
        "max Rb(M, N_RB) s.t. Eb/N0 >= thr(M)",
    ),
    GlossaryEntry(
        CATEGORIES[6],
        "Feasible candidate / Exhaustive search",
        "Kandidat Layak / Pencarian Menyeluruh",
        (
            "[Diimplementasikan di RuralLink] Karena ruang kandidat kecil (4 modulasi x 5 pilihan "
            "RB = 20 kombinasi), src/adaptive.py mengevaluasi seluruh kandidat secara eksak tanpa "
            "aproksimasi heuristik."
        ),
        "|kandidat| <= 4 x 5 = 20",
    ),
    GlossaryEntry(
        CATEGORIES[6],
        "Adaptive bandwidth / Joint adaptation",
        "Alokasi Bandwidth Adaptif / Adaptasi Gabungan",
        (
            "[Diimplementasikan di RuralLink] Mengubah N_RB bersama modulasi (S3) memberi rentang "
            "SNR tambahan +13,98 dB saat mundur ke 1 RB, memperpanjang jangkauan jauh melampaui "
            "adaptasi modulasi saja (S1)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[6],
        "S0 / S1 / S2 / S3 / R0",
        "Skenario Evaluasi RuralLink",
        (
            "[Diimplementasikan di RuralLink] S0: QPSK 25 RB tetap (baseline); S1: modulasi "
            "adaptif"
            "25 RB; S2: bandwidth adaptif QPSK; S3: gabungan modulasi + bandwidth adaptif; R0: "
            "referensi ketahanan BPSK 1 RB tetap."
        ),
        "S0 (QPSK,25), S1 (M,25), S2 (QPSK,RB), S3 (M,RB), R0 (BPSK,1)",
    ),
    GlossaryEntry(
        CATEGORIES[6],
        "Baseline / Robustness reference",
        "Acuan Dasar (S0) / Referensi Ketahanan (R0)",
        (
            "[Diimplementasikan di RuralLink] S0 mewakili konfigurasi tetap pita lebar (laju "
            "tinggi, jangkauan pendek); R0 mewakili batas jangkauan maksimum tetap (BPSK x 1 RB)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[6],
        "Trade-off",
        "Pertukaran Kinerja",
        (
            "[Diimplementasikan di RuralLink] Setiap pengurangan RB atau order modulasi menukar "
            "laju data nominal demi margin SNR dan jangkauan sel yang lebih besar."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[6],
        "Ablation study / Sensitivity analysis",
        "Studi Ablasi / Analisis Sensitivitas",
        (
            "[Diimplementasikan di RuralLink] S1 dan S2 mengisolasi kontribusi masing-masing "
            "derajat kebebasan terhadap S3 (ablasi); kontrol 700 MHz dan BER 10^-3 menguji "
            "sensitivitas parameter."
        ),
        "-",
    ),
    # ================================================================== H
    GlossaryEntry(
        CATEGORIES[7],
        "Monte Carlo",
        "Simulasi Monte Carlo Bit-Level",
        (
            "[Diimplementasikan di RuralLink] Pengiriman bit acak nyata melewati modulator, kanal "
            "AWGN/Rayleigh, ekualiser ZF, dan demodulator untuk memvalidasi kurva teoretis secara "
            "empiris."
        ),
        "N_bits in {10^2, 10^3, 10^4, 10^5, 10^6}",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Random bits / Random seed / RNG",
        "Bit Acak / Benih Acak / Generator Bilangan Acak",
        (
            "[Diimplementasikan di RuralLink] Pembangkit np.random.default_rng(seed=42) "
            "menghasilkan urutan bit dan realisasi kanal yang konsisten lintas strategi dan "
            "frekuensi untuk perbandingan adil."
        ),
        "seed = 42",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Sample size / Realization",
        "Ukuran Sampel / Realisasi Acak",
        (
            "[Diimplementasikan di RuralLink] Jumlah bit Monte Carlo (10^2 s.d. 10^6, diselaraskan "
            "ke kelipatan k) dan 5.000 realisasi bersama shadowing+Rayleigh per titik "
            "jarak. Sampel"
            "kecil (<10^5) berketidakpastian tinggi."
        ),
        "N_draws = 5000 (kurva cakupan)",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Probability distribution / Gaussian / Exponential",
        "Distribusi Probabilitas (Normal & Eksponensial)",
        (
            "[Diimplementasikan di RuralLink] Shadowing mengikuti distribusi Gaussian dalam dB; "
            "daya kanal Rayleigh |h|^2 mengikuti distribusi Eksponensial berataan 1."
        ),
        "X_sigma ~ N(0, sigma^2); |h|^2 ~ Exp(1)",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Confidence interval / Wilson interval",
        "Interval Kepercayaan 95% (Wilson)",
        (
            "[Diimplementasikan di RuralLink] Interval kepercayaan binomial 95% untuk BER simulasi "
            "bit independen; lebih akurat daripada aproksimasi normal saat BER mendekati 0."
        ),
        "z = 1,96 (95% CI Wilson)",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Rule of three / Zero observed errors",
        "Aturan Tiga / Nol Galat Teramati",
        (
            "[Diimplementasikan di RuralLink] Ketika 0 bit salah teramati dari N_bits percobaan "
            "(sering terjadi pada sampel kecil atau SNR tinggi), batas atas BER 95% diestimasi "
            "sebagai 3 / N_bits."
        ),
        "CI_95%(0 error) = [0, min(1, 3 / N_bits)]",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Theoretical vs Simulated result",
        "Hasil Teoretis vs Simulasi",
        (
            "[Diimplementasikan di RuralLink] Seluruh keluaran RuralLink dilabeli THEORETICAL "
            "(rumus tertutup/PL median) atau SIMULATED (realisasi acak shadowing/Rayleigh "
            "dan Monte"
            "Carlo bit-level)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Reproducibility / Validation / Verification",
        "Reproduksibilitas / Validasi / Verifikasi",
        (
            "[Diimplementasikan di RuralLink] Reproduksibilitas dijamin via seed=42 dan config.py; "
            "verifikasi mengecek kebenaran rumus (mis. 6,02 dB, 13,98 dB); validasi mencocokkan MC "
            "terhadap BER teoretis."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Link-level vs System-level simulation",
        "Simulasi Tingkat Tautan vs Tingkat Sistem",
        (
            "[Diimplementasikan di RuralLink] RuralLink adalah simulasi link-level (1 UE, 1 BTS, "
            "bit/simbol/kanal fisik), bukan system-level multi-sel dengan penjadwalan banyak "
            "pengguna."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[7],
        "Field measurement / Extrapolation / Model assumptions",
        "Pengukuran Lapangan / Ekstrapolasi / Asumsi Model",
        (
            "[Diimplementasikan di RuralLink] Parameter CI Park (2023) berasal dari pengukuran "
            "Korea Selatan 1400 MHz dan diekstrapolasi ke 900/1800 MHz tanpa kalibrasi lapangan "
            "wilayah 3T Indonesia."
        ),
        "-",
    ),
    # ================================================================== I
    GlossaryEntry(
        CATEGORIES[8],
        "Reddy 2022",
        "Reddy et al. (2022), EURASIP JWCN",
        (
            "[Konteks literatur / tidak diimplementasikan] Rujukan utama ide pemusatan daya "
            "per PRB"
            "(Eq. 7) dan margin shadowing 95% (1,645 sigma); aslinya memakai 700 MHz MIMO "
            "16-antena"
            "dan HARQ. Di RuralLink hanya menginspirasi model SISO uncoded & opsi suplemen 700 MHz."
        ),
        "DOI: 10.1186/s13638-022-02133-3",
    ),
    GlossaryEntry(
        CATEGORIES[8],
        "Park 2023",
        "Park et al. (2023), IEEE WCL (arXiv:2305.01152v1)",
        (
            "[Diimplementasikan di RuralLink] Sumber model path loss Close-In (Eq. 3) dan "
            "parameter"
            "pedesaan 1400 MHz standar LOS/NLOS (Table II) yang diekstrapolasi ke 900/1800 MHz."
        ),
        "DOI: 10.1109/LWC.2023.3273280",
    ),
    GlossaryEntry(
        CATEGORIES[8],
        "Khan 2025",
        "Khan et al. (2025), Scientific Reports",
        (
            "[Konteks literatur / tidak diimplementasikan] Menginspirasi modulasi adaptif berbasis "
            "ambang pada target BER 10^-2 (Table 9). Persamaan BER-nya tidak disalin karena "
            "menghilangkan faktor 1/log2(M) (Keputusan D10)."
        ),
        "DOI: 10.1038/s41598-025-16743-6",
    ),
    GlossaryEntry(
        CATEGORIES[8],
        "Yogapratama rural LTE study",
        "Yogapratama et al. (2015), Table IV",
        (
            "[Diimplementasikan di RuralLink] Sumber parameter perangkat keras RF uplink (23 dBm, "
            "Gr 11 dBi, L_feeder 5 dB, L_body 3 dB, NF 4 dB, B_ch 5 MHz); PDF lokal hanya berisi "
            "gambar/tabel sehingga kepengarangan dicatat berstatus parsial (Keputusan D9)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[8],
        "Komdigi 2025",
        "Laporan Kinerja Kementerian Komunikasi dan Digital RI (2025)",
        (
            "[Konteks literatur / tidak diimplementasikan] Data konteks nasional: Q2 2025 cakupan "
            "4G mencapai 98,95% populasi namun baru 53,82% luas daratan, dengan 6.747 BTS di "
            "wilayah 3T."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[8],
        "DOI",
        "Digital Object Identifier",
        (
            "[Konteks literatur / tidak diimplementasikan] Pengenal permanen artikel ilmiah agar "
            "rujukan pustaka dapat ditelusuri dan diverifikasi."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[8],
        "Research adaptation vs Replication",
        "Adaptasi Riset vs Replikasi",
        (
            "[Diimplementasikan di RuralLink] RuralLink adalah adaptasi terintegrasi dari beberapa "
            "rujukan pada model terpadu yang disederhanakan, BUKAN replikasi persis Reddy (2022) "
            "atau Khan (2025)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[8],
        "Research contribution / Limitations / Future work",
        "Kontribusi / Keterbatasan / Pekerjaan Lanjutan",
        (
            "[Diimplementasikan di RuralLink] Kontribusi: memisahkan manfaat adaptasi modulasi "
            "(S1), bandwidth (S2), dan gabungan (S3) dengan MC bit-level. Keterbatasan: uncoded, "
            "tanpa interferensi/FEC/data lapangan 3T (menjadi pekerjaan lanjutan)."
        ),
        "-",
    ),
    # ================================================================== J
    GlossaryEntry(
        CATEGORIES[9],
        "Python",
        "Python 3.12",
        (
            "[Diimplementasikan di RuralLink] Bahasa pemrograman utama untuk mesin ilmiah (src/), "
            "eksperimen (experiments/), pengujian (tests/), dan antarmuka (app.py)."
        ),
        "Python 3.12.14 (.venv)",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "Streamlit",
        "Streamlit Interactive Web Framework",
        (
            "[Diimplementasikan di RuralLink] Kerangka kerja UI workbench empat tab (Tab A-D) yang "
            "memanggil langsung mesin src/ secara luring tanpa basis data eksternal."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "NumPy / SciPy / Pandas",
        "Pustaka Komputasi Numerik & Data Python",
        (
            "[Diimplementasikan di RuralLink] NumPy untuk vektorisasi bit/simbol/kanal; SciPy "
            "(erfc, brentq, quad) untuk BER eksak & ambang; Pandas untuk tabel dan ekspor CSV."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "Plotly / Matplotlib",
        "Pustaka Visualisasi Interaktif & Publikasi",
        (
            "[Diimplementasikan di RuralLink] Plotly untuk grafik interaktif di Streamlit (SNR, "
            "konstelasi, zona radial); Matplotlib untuk grafik statis PNG resolusi publikasi di "
            "outputs/figures/."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "CSV / PNG",
        "Comma-Separated Values / Portable Network Graphics",
        (
            "[Diimplementasikan di RuralLink] Format keluaran riset tervalidasi di "
            "outputs/results/"
            "dan outputs/figures/ yang dapat diunduh dari Tab B serta kamus CSV di Tab D."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "Scientific engine",
        "Mesin Ilmiah (src/)",
        (
            "[Diimplementasikan di RuralLink] Lima modul tervalidasi (propagation, link_budget, "
            "modulation, channels, metrics) ditambah adaptive.py yang terisolasi dari kode "
            "tampilan"
            "UI."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "Automated testing",
        "Pengujian Otomatis (pytest, AppTest, Ruff)",
        (
            "[Diimplementasikan di RuralLink] Verifikasi otomatis identitas analitis, validasi MC, "
            "AppTest UI Streamlit, dan kualitas/format kode dengan Ruff sebelum setiap rilis."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "Git and GitHub",
        "Kontrol Versi Git & Repositori GitHub",
        (
            "[Diimplementasikan di RuralLink] Pengelolaan riwayat perubahan terstruktur per "
            "fitur/fase (termasuk integrasi prototipe Zahran dan cabang workbench interaktif)."
        ),
        "-",
    ),
    GlossaryEntry(
        CATEGORIES[9],
        "Deployment / Offline execution",
        "Penerapan (Streamlit Cloud) & Eksekusi Luring",
        (
            "[Diimplementasikan di RuralLink] Dirancang kompatibel Streamlit Community Cloud "
            "(requirements.txt) sekaligus berjalan penuh secara luring via run_local.ps1 "
            "tanpa aset"
            "jaringan."
        ),
        "-",
    ),
)


def glossary_dataframe(category: str | None = None, query: str = "") -> pd.DataFrame:
    """Return filtered glossary entries as a 4-column display DataFrame."""
    rows = ENTRIES
    if category and category != "Semua kategori":
        rows = tuple(e for e in rows if e.kategori == category)
    q = query.strip().lower()
    if q:
        rows = tuple(
            e
            for e in rows
            if q in e.istilah.lower()
            or q in e.kepanjangan.lower()
            or q in e.penjelasan.lower()
            or q in e.persamaan.lower()
            or q in e.kategori.lower()
        )
    return pd.DataFrame(
        [
            {
                "Istilah / Singkatan": e.istilah,
                "Kepanjangan / Nama lengkap": e.kepanjangan,
                "Penjelasan & Relevansi RuralLink": e.penjelasan,
                "Persamaan / Simbol / Nilai": e.persamaan,
            }
            for e in rows
        ]
    )


def glossary_csv_bytes() -> bytes:
    """Return full encyclopedia (including category) as UTF-8 BOM CSV bytes for Excel/group use."""
    df = pd.DataFrame(
        [
            {
                "Kategori": e.kategori,
                "Istilah / Singkatan": e.istilah,
                "Kepanjangan / Nama lengkap": e.kepanjangan,
                "Penjelasan & Relevansi RuralLink": e.penjelasan,
                "Persamaan / Simbol / Nilai": e.persamaan,
            }
            for e in ENTRIES
        ]
    )
    return df.to_csv(index=False).encode("utf-8-sig")


def render_glossary_markdown() -> str:
    """Generate docs/GLOSSARY.md directly from ENTRIES so documentation never drifts."""
    lines = [
        "# Kamus Istilah Teknis & Persamaan (Ensiklopedia RuralLink)",
        "",
        f"Total entri: **{len(ENTRIES)}** istilah dalam **{len(CATEGORIES)}** kategori. "(
            "Dokumen ini dihasilkan langsung dari `glossary_data.py` agar selalu konsisten dengan "
            "Tab D di aplikasi Streamlit."
        ),
        "",
        "Penanda status pada setiap entri:",
        "- `[Diimplementasikan di RuralLink]` — aktif dihitung oleh `src/` atau `config.py`.",
        "- `[Latar belakang teoretis]` — konsep dasar telekomunikasi yang melandasi model.",
        (
            "- `[Konteks literatur / tidak diimplementasikan]` — dibahas dalam rujukan atau "
            "batasan, tidak dimodelkan di mesin."
        ),
        "",
    ]
    for cat in CATEGORIES:
        cat_entries = [e for e in ENTRIES if e.kategori == cat]
        lines.extend(
            [
                f"## {cat} ({len(cat_entries)} istilah)",
                "",
                (
                    "| Istilah / Singkatan | Kepanjangan / Nama lengkap | Penjelasan & Relevansi "
                    "RuralLink | Persamaan / Simbol / Nilai |"
                ),
                "|---|---|---|---|",
            ]
        )
        for e in cat_entries:
            lines.append(f"| {e.istilah} | {e.kepanjangan} | {e.penjelasan} | {e.persamaan} |")
        lines.append("")
    return "\n".join(lines)
