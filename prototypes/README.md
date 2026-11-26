# Prototipe UI (referensi visual, bukan mesin ilmiah)

Direktori ini mengarsipkan file HTML/CSS/JS standalone karya **Zahran** (riwayat dan penulis Git asli dipertahankan):

- `dashboard_rurallink.html` — versi prototipe awal yang menginspirasi tata letak aplikasi Streamlit (`app.py`).
- `dashboard_interaktif_siskom.html` — versi terbaru buatan Zahran yang dijadikan fondasi langsung antarmuka web native (`public/index.html`) di atas API FastAPI (`api/index.py`).

**Jangan dipakai untuk angka penelitian.** Prototipe HTML standalone ini memuat pendekatan yang sengaja diganti oleh mesin Python tervalidasi (`src/`):

- daya pancar campuran 23–46 dBm (uplink/downlink), sedangkan simulasi uplink membatasi UE maksimal 23 dBm;
- bandwidth tetap 5 MHz dan batas SNR universal LTE `-6,9 dB`, tanpa alokasi PRB (`1..25 RB`) dan ambang per-modulasi Cho–Yoon;
- parameter difraksi tanpa profil elevasi medan dan pendekatan Rician melalui pengali SNR Rayleigh;
- konstelasi sintetis 16-QAM saja tanpa simulasi Monte Carlo bit-level.

Semua perhitungan final berasal dari `src/` (Python).
