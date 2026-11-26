# Prototipe UI (referensi visual, bukan mesin ilmiah)

`dashboard_rurallink.html` adalah dashboard HTML/CSS/JS standalone buatan Zahran (riwayat dan
penulis Git asli dipertahankan). File ini menjadi fondasi desain visual aplikasi Streamlit
(`app.py`): rail parameter di kiri, kontrol segmented, telemetry strip, kurva SNR, konstelasi,
dan peta zona radial.

**Jangan dipakai untuk angka penelitian.** Prototipe ini memuat hal yang sengaja tidak diwarisi
aplikasi final:

- frekuensi 700 MHz (di luar cakupan penelitian 900/1800 MHz) dan daya UE sampai 26 dBm (batas 23 dBm);
- pendekatan BER QAM dan ambang SNR yang berbeda dari mesin Python tervalidasi;
- rata-rata BER Rayleigh dipakai untuk adaptasi sesaat;
- konstelasi sintetis 16-QAM hanya AWGN, tanpa transmisi Monte Carlo bit-level.

Semua perhitungan final berasal dari `src/` (Python). Buka file ini langsung di browser untuk
melihat desain aslinya.
