# Benchmark Gemini untuk CLI dan panduan memilih model

**25 November 2026, WIB · Fokus pada Gemini 4 Carbon, Neon, Argon, dan Hydrogen**

## Pilihan dalam 30 detik

| Tugas di terminal | Pilihan awal | Kapan pindah |
| --- | --- | --- |
| Edit kecil, boilerplate, docs, skrip, formatting, test dengan perilaku yang sudah jelas | **Hydrogen Low atau Medium** | Ke High kalau test mulai mengungkap masalah lintas modul |
| Bug biasa, upgrade dependensi dengan test, refactor mekanis lintas file | **Hydrogen High** | Ke Neon High jika penyebab bug atau dampak perubahan masih ambigu |
| Memahami repo asing, memperbaiki bug lintas komponen, implementasi fitur dengan beberapa keputusan desain | **Neon High** | Coba Neon xHigh bila hipotesis masih bersaing atau dua percobaan menghasilkan diagnosis yang sama-sama lemah |
| Patch besar dengan rencana dan kriteria penerimaan yang jelas | **Orchestrator (Neon)**, jika tersedia | Pilih Neon atau Carbon langsung jika implementasi terus memerlukan keputusan arsitektur baru |
| Migrasi lintas repo, protokol, concurrency, build system yang sulit, atau analisis banyak artefak | **Carbon High** atau **Neon xHigh** | Carbon untuk eksplorasi panjang dan keputusan yang saling terkait, Neon xHigh untuk diagnosis, pemahaman repo, dan verifikasi |
| Generate test untuk kode yang rumit | **Hydrogen High**, coba **xHigh** untuk invariant dan edge case | Ke Neon High bila spesifikasi kontraknya harus disimpulkan dulu |
| Pemeliharaan workflow yang sudah dipatok ke Argon | **Migrasikan ke Neon High** untuk reasoning atau **Hydrogen High** untuk eksekusi | Jalankan ulang test pada workflow sebelum mengganti model default |
| Akun Free, Google AI Plus, atau Pro trial standar | **Hydrogen** | Pakai High atau xHigh hanya ketika tugasnya membutuhkan lebih banyak penalaran |

**Hydrogen** untuk volume, **Neon** untuk coding yang ambigu, **Carbon** untuk tugas terminal paling berat, dan **Orchestrator** untuk memadukan perencanaan dengan eksekusi. Argon masih kompetitif pada beberapa pengujian, tetapi Google menjadwalkan penghapusannya dari Antigravity pada **30 November 2026**. [Terminal-Bench 4.1](https://www.tbench.ai/?efforts=all&version=4.1) · [Artificial Analysis Coding Agent Index](https://artificialanalysis.ai/agents/coding-agents/antigravity-cli) · [Scale SWE Atlas](https://labs.scale.com/leaderboard/swe-atlas?tab=overall) · [Model Antigravity](https://antigravity.google/docs/models).

### Ruang lingkup

Laporan ini membandingkan **semua model reasoning Gemini 4 reguler yang relevan untuk coding di terminal pada tanggal di atas**, serta model Gemini 3 yang masih relevan untuk akun enterprise, API, atau migrasi dari CLI lama. Varian Gemini Live, Omni, Nano Banana, dan Embedding punya fungsi khusus dan dicatat di bagian katalog. Angka berasal dari pengujian publik. Saya tidak menjalankan model berbayar di repo Anda, sehingga pemilihan per tugas adalah rekomendasi berbasis bukti publik. [Katalog model Google Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models) · [Model Antigravity](https://antigravity.google/docs/models).

## 1. CLI mana yang Anda pakai?

| Permukaan | Bisa dipakai untuk apa | Implikasi |
| --- | --- | --- |
| **Antigravity CLI, `agy`** | CLI Google untuk akun pribadi dan juga bisa terhubung ke jalur enterprise/API | Ini lingkungan pengujian untuk tabel CLI utama. Jalankan `agy models` dengan autentikasi yang akan Anda pakai |
| **Gemini CLI open-source, `gemini`** | Proyek lama yang tetap dipelihara, dengan jalur Gemini Code Assist Standard/Enterprise, Cloud, dan API berbayar yang sesuai | Akun pribadi Free, Pro, dan Ultra berhenti dilayani melalui jalur akun lama pada 18 Juni 2026. Katalog dan alias berbeda menurut versi, penyedia, dan autentikasi |
| **Gemini Developer API / Gemini Enterprise Agent Platform** | Memanggil model dari program, atau dari CLI yang mendukung penyedia tersebut | Model ID API dasar seperti `gemini-4-neon` berbeda dari opsi CLI yang menyertakan effort seperti `gemini-4-neon-xhigh` |
| **CLI lain dengan backend Gemini** | Menjalankan model melalui integrasi Aider, OpenHands, atau agent milik sendiri, jika integrasinya mendukung ID dan tool yang diperlukan | Skor untuk `agy` hanya mengukur kombinasi model dan harness yang diuji |

*Harness* adalah perangkat lunak yang memberi model instruksi, alat shell dan file, pengelolaan konteks, batas percobaan, dan cara menjalankan atau memeriksa hasil. Issue dukungan Neon/Hydrogen pada repositori `gemini` masih menunjukkan permintaan dukungan pada snapshot yang diperiksa. Cek `gemini models` atau `gemini --list-models` pada versi yang sudah memiliki model discovery. Pada `agy`, changelog mendokumentasikan Neon melalui Gemini API key sejak 1.5.12 serta ADC dan enterprise gateway sejak 1.5.13. [Pengumuman transisi Google](https://github.com/google-gemini/gemini-cli/discussions/27274) · [Pemberitahuan 18 Juni](https://github.com/google-gemini/gemini-cli/discussions/28017) · [Issue Gemini CLI #30385](https://github.com/google-gemini/gemini-cli/issues/30385) · [Rilis Gemini CLI](https://geminicli.com/docs/changelogs/) · [Changelog Antigravity](https://antigravity.google/docs/changelog?tab=hub).

## 2. Identitas, effort, dan akses

| Model | Rilis di katalog Cloud | ID API | Effort yang didokumentasikan | Akses model langsung di Antigravity |
| --- | --- | --- | --- | --- |
| **Carbon** | 10 Nov | `gemini-4-carbon` | Low, Medium, High | Pro berbayar, trial perangkat premium yang memenuhi syarat, Ultra, Enterprise |
| **Neon** | 18 Nov | `gemini-4-neon` | Low, Medium, High, xHigh | Pro berbayar, trial perangkat premium yang memenuhi syarat, Ultra, Enterprise |
| **Argon** | 13 Okt | `gemini-4-argon` | Low, Medium, High | Pro berbayar, trial perangkat premium yang memenuhi syarat, Ultra, Enterprise hingga perubahan Antigravity 30 Nov |
| **Hydrogen** | 12 Nov | `gemini-4-hydrogen` | Low, Medium, High, xHigh | Free, Plus, Pro termasuk trial standar, Ultra, Enterprise |

Google Cloud mendokumentasikan **1.048.576 token gabungan input + output** pada keempat model. Output mencakup reasoning, tool call, dan jawaban final. Satu segmen foreground pada Neon/Hydrogen dapat menghasilkan sampai 65.536 token. Pada Carbon/Argon, batas segmen tercatat 65.536 untuk streaming dan 32.768 untuk non-streaming. *Long decodes* pada API yang mendukungnya bisa melanjutkan antarsegmen dalam anggaran konteks yang sama. Praktiknya, instruksi agen, hasil tool, riwayat, dan konteks repo ikut memakai anggaran. Kapasitas 1M juga berbeda dari kemampuan mengambil detail tertentu dengan akurat. Untuk gambar, PDF, diagram, audio atau video, cek dukungan input pada endpoint dan cara agen meneruskan lampiran. [Neon Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon) · [Carbon Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-carbon) · [Hydrogen Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-hydrogen) · [Argon Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-argon).

Dokumentasi tingkat effort berbeda menurut permukaan. Dokumentasi pemilih Antigravity mencantumkan Medium sebagai default untuk Neon dan blog Antigravity mencantumkan Medium untuk Hydrogen. Cloud API mendokumentasikan High sebagai default keduanya. `/effort` menampilkan konfigurasi aktif. Untuk pengujian dan automasi, pilih effort eksplisit. Penghapusan Argon dari pemilih Antigravity punya jadwal tersendiri. Katalog Cloud mencantumkan tanggal pensiun `gemini-4-argon` **13 Oktober 2027 atau sesudahnya**. [Pemilih model](https://antigravity.google/docs/models) · [Blog Hydrogen di Antigravity](https://antigravity.google/blog/gemini-4-hydrogen-in-google-antigravity) · [Perintah effort](https://antigravity.google/docs/cli/commands/effort/) · [Lifecycle Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions).

**Tool use dan output terstruktur.** Keempatnya mendukung function calling dan structured output pada Cloud. Dokumen model juga mencantumkan implicit caching dengan minimum 4.096 token. Ini relevan untuk agent yang berulang kali mengirim instruksi dan konteks repo yang sama. File Office dan OpenDocument dapat diterima pada endpoint yang mendukungnya. Dukungan di CLI mengikuti alat dan jalur penyedia yang dipakai. [Neon Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon) · [Carbon Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-carbon) · [Hydrogen Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-hydrogen) · [Argon Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-argon).

## 3. Benchmark yang menjalankan Antigravity CLI

### 3.1 Terminal-Bench 4.1, leaderboard penerbit

Terminal-Bench menilai apakah agen menyelesaikan tugas di lingkungan terminal dengan verifikasi, sehingga relevan untuk pekerjaan yang mencampur shell, kode, artefak, dan konfigurasi. Versi 4.1 memperbarui verifier dan menggunakan kembali artefak run sebelumnya ketika tersedia. Angka ± adalah interval keyakinan 95% yang ditampilkan leaderboard. [Leaderboard 4.1](https://www.tbench.ai/?efforts=all&version=4.1) · [Catatan rilis 4.1](https://www.tbench.ai/news/terminal-bench-4-1).

| Model di Antigravity CLI | Resolusi 4.1 | Posisi saat snapshot, semua effort | Token / biaya yang tercantum untuk run leaderboard |
| --- | ---: | ---: | ---: |
| **Carbon High** | **64,5% ± 3,2** | 4 | 3,8 miliar / sekitar $1.400 |
| **Neon xHigh** | **61,2% ± 2,8** | 8 | 3,2 miliar / sekitar $1.900 |
| **Hydrogen High** | **56,4% ± 3,0** | 16 | 3,6 miliar / sekitar $800 |
| **Argon High** | **55,5% ± 2,8** | 17 | 2,8 miliar / sekitar $1.100 |

Carbon memimpin Neon **3,3 poin persentase** pada run penerbit. Interval marginalnya tumpang tindih dan tidak tersedia pengujian berpasangan di tabel, jadi selisih ini belum cukup untuk menyatakan Carbon selalu lebih baik. Hydrogen dan Argon berjarak **0,9 poin**. Kedua hasil tidak cukup untuk mengurutkan mereka secara meyakinkan. Biaya tabel adalah total run yang tercantum dan rentan terhadap perbedaan harga token antartanggal. [Leaderboard 4.1](https://www.tbench.ai/?efforts=all&version=4.1).

### 3.2 Artificial Analysis Coding Agent Index v2.1, pengujian independen

Artificial Analysis menguji empat kombinasi berikut dengan Antigravity CLI. Skor indeks menggabungkan FrontierCode-AA 2.0, Terminal-Bench 4.1, dan SWE-Atlas-QnA-AA. Biaya, waktu, dan token adalah metrik per tugas yang dilaporkan untuk suite tersebut. [Halaman Antigravity CLI](https://artificialanalysis.ai/agents/coding-agents/antigravity-cli) · [Tabel empat konfigurasi](https://artificialanalysis.ai/agents/coding-agents/comparisons/antigravity-cli-vs-grok-build).

| Model + effort | Coding Agent Index | FrontierCode-AA 2.0 | Terminal-Bench 4.1 | SWE-Atlas-QnA-AA | USD/tugas | Menit/tugas | Token/tugas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Neon xHigh** | **59** | **43** | **65** | **68** | $6,86 | **30,5** | **13,8 juta** |
| **Carbon High** | 55 | 38 | **65** | 64 | $9,75 | 33,6 | 15,4 juta |
| **Hydrogen xHigh** | 52 | 37 | 60 | 60 | **$4,45** | 32,1 | 18,5 juta |
| **Argon High** | 45 | 25 | 57 | 55 | $13,67 | 37,7 | 16,4 juta |

- **Neon xHigh vs Carbon High.** +4 poin indeks dan sekitar **30% lebih murah per tugas**, sekaligus 3,1 menit lebih cepat pada suite ini.
- **Hydrogen xHigh vs Neon xHigh.** 7 poin indeks lebih rendah dengan biaya per tugas sekitar **35% lebih rendah**. Jumlah token lebih tinggi, sehingga harga per token membantu menjelaskan mengapa totalnya tetap lebih murah.
- **Argon High vs Hydrogen xHigh.** Argon mencatat 7 poin indeks lebih rendah dan biaya sekitar **3,1×** Hydrogen pada suite ini. Kesimpulan lintas jenis tugas tetap perlu melihat tabel SWE Atlas di bawah.

DeepMind melaporkan Neon **65,2%** dan Hydrogen **57,0%** pada baris Terminal-Bench 4.1 di model card masing-masing. Metodologi Neon menyebut hasil Artificial Analysis dengan Antigravity CLI **1.5.9**. Papan penerbit sendiri menampilkan **61,2%** untuk Neon xHigh dan **56,4%** untuk Hydrogen High. Simpan angka sesuai sumber dan konfigurasi aslinya. Angka Neon dari model card dan run Artificial Analysis tidak layak dihitung sebagai dua replikasi independen. [Metodologi Neon](https://storage.googleapis.com/deepmind-media/gemini/gemini_4_neon_model_evaluation.pdf) · [Model card Hydrogen](https://deepmind.google/models/model-cards/gemini-4-hydrogen/) · [Leaderboard penerbit](https://www.tbench.ai/?efforts=all&version=4.1).

### 3.3 Scale Labs SWE Atlas, pengujian independen

Ini pengujian tambahan yang memakai Antigravity CLI untuk keempat model. QnA menguji pemahaman codebase. Test Writing dan Refactoring menguji jenis perubahan yang lebih spesifik. Skor dan nilai ± mengikuti publikasi masing-masing kategori. [Overall](https://labs.scale.com/leaderboard/swe-atlas?tab=overall) · [QnA](https://labs.scale.com/leaderboard/swe-atlas?tab=qna) · [Test Writing](https://labs.scale.com/leaderboard/swe-atlas?tab=testwriting) · [Refactoring](https://labs.scale.com/leaderboard/swe-atlas?tab=refactoring).

| Model + effort | Overall | QnA | Test Writing | Refactoring |
| --- | ---: | ---: | ---: | ---: |
| **Neon xHigh** | **72,01 ± 5,45** | **79,84 ± 7,16** | 73,33 ± 9,31 | 62,86 ± 11,60 |
| **Carbon High** | 71,45 ± 5,46 | 73,39 ± 7,89 | 76,67 ± 8,91 | 64,29 ± 11,51 |
| **Hydrogen xHigh** | 71,98 ± 5,44 | 75,00 ± 7,73 | 76,67 ± 8,91 | 64,29 ± 11,51 |
| **Argon High** | 70,08 ± 5,48 | 65,32 ± 8,49 | **77,78 ± 8,76** | **67,14 ± 11,28** |

Neon dan Hydrogen hanya berjarak **0,03 poin** di Overall. Hydrogen juga mencatat angka yang sama dengan Carbon pada Test Writing dan Refactoring. Argon punya skor titik tertinggi di dua kategori itu, dengan interval lebar yang bertumpang tindih. Untuk refactor mekanis atau pekerjaan menulis test, data ini mendukung memulai dari Hydrogen. Untuk tugas seperti “jelaskan bagaimana transaksi melintasi queue, worker, dan database”, Neon punya dukungan yang lebih konsisten dari QnA Scale dan QnA Artificial Analysis. [Scale SWE Atlas](https://labs.scale.com/leaderboard/swe-atlas?tab=overall) · [Artificial Analysis](https://artificialanalysis.ai/agents/coding-agents/antigravity-cli).

Scale juga mencatat **Argon High 92,16** pada **SWE-Bench Pro V2** dengan **mini-swe-agent**. Dataset, protokol, dan harness berbeda dari SWE Atlas, SWE-bench Verified, dan Terminal-Bench. Data ini berguna untuk menilai Argon pada protokol tersebut. Saya tidak menemukan deretan yang memadai untuk membandingkan keempat model pada SWE-Bench Pro V2 dengan konfigurasi yang sama. [Scale SWE-Bench Pro V2](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2).

## 4. Hasil independen di luar pengujian CLI utama

### 4.1 Vals AI untuk coding, migrasi, dan pekerjaan dokumen

Berikut snapshot leaderboard Vals **21 November 2026**. Biaya memakai kolom *Cost/test* pada halaman yang sama. Angka historis di pengumuman model bisa berbeda. Misalnya, artikel peluncuran Vals untuk Neon menyebut 70,87%, sedangkan headline leaderboard yang diperiksa memuat 69,23%. [Vals Index](https://www.vals.ai/benchmarks/vals_index) · [Laporan peluncuran Vals untuk Neon](https://www.vals.ai/models/google_gemini-4-neon).

| Model | Vals Index | USD/test | Terminal-Bench 4 di Vals | Vibe Code Bench v1.1.1 | Code Migration v1.1 | Legal Research | Tax Agent |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **Neon** | **69,23%** | **$7,40** | 61,6% | **80,2%** | 75,8% | **56,3%** | **54,9%** |
| **Carbon** | 68,83% | $10,51 | **63,1%** | 75,8% | 80,1% | 55,8% | 51,8% |
| **Hydrogen** | 67,07% | $7,75 | 54,0% | 76,2% | **82,7%** | 53,8% | 52,3% |
| **Argon** | 67,37% | $10,58 | 57,6% | 75,4% | 74,4% | 54,8% | 49,2% |

Nilai **82,7% Hydrogen** pada Code Migration mendukung pemakaian Hydrogen untuk migrasi yang langkah dan validasinya jelas. Migrasi yang memerlukan desain kontrak baru, rollback lintas layanan, atau banyak keputusan berurutan tetap layak dimulai dengan Carbon atau Neon sebagai perencana. Pada beban campuran Vals ini, Neon bisa lebih murah per tugas daripada Hydrogen meski tarif tokennya dua kali lebih tinggi. Bandingkan biaya aktual per pekerjaan selesai. [Vals Index](https://www.vals.ai/benchmarks/vals_index) · [Vals Hydrogen](https://www.vals.ai/models/google_gemini-4-hydrogen).

### 4.2 Arena untuk coding interaktif, frontend, dan penulisan

**Agent Arena Index, 22 November.** Di leaderboard gabungan, Neon xHigh berada di posisi 3, Carbon High di 4, Hydrogen xHigh di 9, dan Argon High di 14. Hasil Neon dan Hydrogen masih berlabel *Preliminary*. Ini berdasarkan sesi agen dan penilaian pengguna. [Agent Arena Index](https://arena.ai/leaderboard/agent).

**WebDev Arena, 23 November.** Carbon High berada di posisi 4, Neon xHigh di 5, dan Hydrogen xHigh di 14. Carbon mencatat rating 1.769 pada papan itu. Untuk UI dengan spesifikasi longgar atau banyak keputusan desain, saya akan memilih Carbon High atau Neon High/xHigh. Untuk scaffolding, menghubungkan komponen yang sudah ada, dan iterasi CSS dengan acuan jelas, saya akan memulai dari Hydrogen. Arena WebDev memberi sinyal kualitas web app yang dinilai pengguna. Keberhasilan test lokal, aksesibilitas, dan kecocokan dengan komponen repo tetap perlu diukur dari hasilnya. [WebDev Arena](https://arena.ai/leaderboard/code/webdev).

**Text Arena.** Snapshot konfigurasi *raw, by lab* menampilkan Carbon dan Argon di depan Neon dan Hydrogen. Itu menjelaskan mengapa Argon masih dapat terasa bagus untuk sintesis atau penulisan meski posisinya lebih rendah pada suite coding CLI. [Text Arena](https://arena.ai/leaderboard/chat/text?rankBy=lab&scoring=raw).

### 4.3 Kecerdasan umum, latensi, throughput, dan biaya dengan Artificial Analysis

Intelligence Index v5.0.2 berbeda dari **Coding Agent Index v2.1** di bagian 3.2. *Time to first answer token* mencakup waktu reasoning sebelum teks jawaban tampak. Kecepatan, waktu, dan biaya di sini adalah pengukuran API dan suite model pada snapshot yang diperiksa. Waktu menyelesaikan satu pekerjaan CLI juga dipengaruhi pembacaan file, panggilan tool, kompilasi, retry, dan persetujuan. [Metodologi dan perbandingan model Google](https://artificialanalysis.ai/models/creators/google).

| Model + effort | Intelligence Index | Waktu ke token jawaban pertama | Output | Waktu/tugas indeks | USD/tugas indeks |
| --- | ---: | ---: | ---: | ---: | ---: |
| **Neon xHigh** | **62** | 60,05 dtk | 92 token/dtk | 25,6 menit | $6,44 |
| **Carbon High** | 60 | 70,50 dtk | 58 token/dtk | 35,2 menit | $7,76 |
| **Hydrogen xHigh** | 54 | 56,32 dtk | **162 token/dtk** | **15,9 menit** | **$3,16** |
| **Argon High** | 51 | **37,46 dtk** | 82 token/dtk | 23,8 menit | $9,95 |

Sumber angka per model ada di [Neon](https://artificialanalysis.ai/models/gemini-4-neon) · [Carbon](https://artificialanalysis.ai/models/gemini-4-carbon/) · [Hydrogen](https://artificialanalysis.ai/models/gemini-4-hydrogen) · [Argon](https://artificialanalysis.ai/models/gemini-4-argon).

**Effort lebih tinggi memiliki biaya yang nyata.** Halaman pembanding Artificial Analysis menampilkan Neon High dan Carbon High sama-sama **60** setelah pembulatan. Neon Medium tercatat **55** dan Carbon Medium **58**. Hydrogen Low, Medium, dan High masing-masing memakai sekitar **1,5 / 3,9 / 8,2 menit** dan **$0,29 / $0,80 / $1,87** per tugas indeks. Hydrogen xHigh mencapai **15,9 menit dan $3,16**. Untuk batch pendek, keuntungan dari menurunkan effort dapat lebih besar dibanding mengganti model. [Pembanding model Google](https://artificialanalysis.ai/models/creators/google) · [Hydrogen](https://artificialanalysis.ai/models/gemini-4-hydrogen).

## 5. Model card DeepMind menurut kemampuan

Tabel ini hanya memuat baris yang relevan untuk memilih agen dan jelas asal-usulnya. Angka dari kartu berbeda bisa memakai effort, alat, tanggal, dan metode yang berbeda. Tanda **—** berarti kartu yang dipakai di sini tidak memberikan angka untuk baris tersebut. [Card Neon](https://deepmind.google/models/model-cards/gemini-4-neon/) · [Card Carbon](https://deepmind.google/models/model-cards/gemini-4-carbon/) · [Card Hydrogen](https://deepmind.google/models/model-cards/gemini-4-hydrogen/) · [Card Argon](https://deepmind.google/models/model-cards/gemini-4-argon/).

| Kemampuan | Benchmark | Carbon | Neon | Argon | Hydrogen |
| --- | --- | ---: | ---: | ---: | ---: |
| Mengikuti relasi pada konteks besar | GraphWalks, 256K–1M, BFS F1 | **96,2%** | 95,2% | 84,2% | — |
| Pekerjaan agen dengan rubrik | Agents’ Last Exam v1.1 | **77,4%** | 75,8% | 69,0% | 71,6% |
| Penggunaan desktop | OSWorld-2.1, subset offline | **81,5%** | — | 74,7% | 77,6% |
| Otomasi pengetahuan | AutomationBench, Zapier | 53,9% | **56,3%** | 51,3% | — |
| Simulasi agen jangka panjang | Vending-Bench 2, saldo akhir | $16.484 | **$16.843** | $13.718 | $14.549 |
| Memahami grafik | Chartography | 72,5% | **73,5%** | 71,6% | 66,6% |
| Penalaran multimodal | MKA, Climb WSR | — | **56,5%** | — | 53,4% |
| Memahami video panjang | LVBench | — | 89,0% | **91,7%** | — |
| Matematika | RiemannBench | 80,0% | **84,0%** | 76,0% | — |
| Sains menggunakan lingkungan terminal | Terminal-Bench-Science 0.1 | 64,8% (AA) | 70,5% | 52,9% (AA) | 51,4% |
| Penalaran tingkat lanjut | HLE-Diamond | — | **71,3%** | — | 58,8% |
| Tugas engineering kompleks | FrontierSWE v2 | **61,2%** | — | 55,0% | — |
| Coding agen, pengujian Cursor | CursorBench 4.1 | — | 65,4% | — | — |

Sumber angka Vending-Bench 2 Neon ada di [pengumuman Neon](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/). Angka Sains Argon **52,9%** mengikuti kartu Carbon yang melaporkan run AA, sedangkan kartu Argon mencatat **57,6%** dalam konfigurasi lain. Hydrogen mencatat **76,1%** pada **AutomationBench-AA**, yang memakai varian benchmark berbeda dari AutomationBench Zapier. [Card Carbon](https://deepmind.google/models/model-cards/gemini-4-carbon/) · [Card Argon](https://deepmind.google/models/model-cards/gemini-4-argon/) · [Card Hydrogen](https://deepmind.google/models/model-cards/gemini-4-hydrogen/).

**Seberapa besar pengaruh harness?** Pada SWE-sweep, DeepMind melaporkan **39,0%** untuk Neon dengan Antigravity CLI 1.5.9 dan **12,8%** dengan mini-swe-agent. Keduanya dilaporkan sebagai *subtask-weighted reward* dalam metodologi Neon. Perbedaan alat, termasuk cara agen membagi pencarian lintas repo, ikut menjelaskan mengapa skor satu kombinasi tidak berlaku otomatis ke kombinasi lain. Metode ini juga berbeda dari SWE-bench Verified dan SWE Atlas. [Metodologi Neon](https://storage.googleapis.com/deepmind-media/gemini/gemini_4_neon_model_evaluation.pdf).

**Implikasi untuk repo besar.** GraphWalks mendukung Carbon/Neon bila perlu menghubungkan banyak bagian dari dokumentasi, log, dan kode. Selisih Carbon–Neon hanya satu poin di evaluasi itu. Mulai dari file yang terkait langsung, arahkan agen memeriksa referensi penting, kemudian perluas konteks bila ada hipotesis yang harus diuji. GraphWalks mengukur penelusuran relasi dan tidak mengukur kualitas patch akhir. [Card Carbon](https://deepmind.google/models/model-cards/gemini-4-carbon/) · [Card Neon](https://deepmind.google/models/model-cards/gemini-4-neon/).

## 6. Harga, kuota, dan biaya per pekerjaan

**Gemini Developer API, tarif standar USD per 1 juta token.** Token output mencakup thinking. Angka di bawah untuk model reguler dan input yang ditagih sesuai tabel Developer API. Jalur Cloud regional, batch, kapasitas terpesan, dan Antigravity memiliki aturan masing-masing. [Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing) · [Cloud pricing](https://cloud.google.com/model-garden/pricing).

| Model | Input / cache hit / output sampai 30 Nov | Mulai 1 Des 2026 | Developer API Free Tier pada halaman harga |
| --- | ---: | ---: | --- |
| **Hydrogen** | $1,50 / $0,075 / $7,50 | Tarif yang tercantum sama | Tercantum tersedia, sesuai limit proyek |
| **Neon** | $3,00 / $0,15 / $15,00 | Tarif yang tercantum sama | Tidak tersedia |
| **Carbon** | $2,00 / $0,10 / $10,00 | **$4,00 / $0,20 / $20,00** | Tidak tersedia |
| **Argon** | $2,00 / $0,10 / $10,00 | **$4,00 / $0,20 / $20,00** | Tidak tersedia |

Contoh hitung untuk **100.000 token input biasa, 200.000 token input cache hit, dan 20.000 token output termasuk thinking**. Biayanya **$0,315 Hydrogen**, **$0,630 Neon**, dan **$0,420 Carbon atau Argon hingga 30 Nov**, lalu **$0,840** untuk Carbon atau Argon mulai 1 Des. Estimasi ini menggunakan jumlah token yang ditagih, tanpa biaya tool, cache write, kapasitas regional, atau retry. Pada pekerjaan agen yang terdiri dari banyak giliran, jumlah input kumulatif bisa melampaui ukuran jendela konteks karena agen melakukan beberapa panggilan model. [Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing) · [Cloud pricing](https://cloud.google.com/model-garden/pricing).

**Dengan langganan Antigravity**, kuota dasar Gemini dibagi dan pemakaiannya bergantung pada pekerjaan yang dilakukan agen. Jadi jumlah prompt yang muat dalam satu periode dapat berbeda. Pengguna Free/Plus memiliki refresh mingguan menurut dokumentasi. Pro atau Ultra dapat memakai AI credits untuk kelebihan pemakaian sesuai pengaturan. Gunakan angka harga API untuk workflow yang memang ditagih melalui API, dan periksa pemakaian kuota akun untuk workflow berlangganan. [Paket Antigravity](https://antigravity.google/docs/plans?hl=en).

## 7. Orchestrator dan kapan menggunakannya

| Mode di Antigravity CLI | Planner / reviewer | Eksekutor | Penggunaan yang cocok |
| --- | --- | --- | --- |
| **Orchestrator (Neon)** | Neon | Hydrogen | Fitur biasa yang menyentuh banyak file, debug beberapa modul, rencana revisi yang bisa diverifikasi |
| **Orchestrator (Carbon)** | Carbon | Hydrogen | Rencana besar dan keputusan kompleks diikuti fase eksekusi yang cukup mekanis |
| **Orchestrator (Argon)** | Argon | Hydrogen | Perbandingan historis dan transisi workflow sampai perubahan katalog |
| **Enterprise / ADC dengan `gemini-pro-orchestrator`** | Carbon High | Hydrogen High | Workflow enterprise di mana kedua model tersedia |
| **Model langsung** | Model yang dipilih | Model yang dipilih | Penalaran harus berlanjut saat agen membaca hasil test, mengubah rencana, dan mengedit kode |

Orchestrator memakai satu sesi dengan pergantian model antara perencanaan, implementasi, dan peninjauan. Dokumentasi `agy` mencantumkan pemilih planner untuk Pro/Ultra. Ketersediaan pilihan spesifik mengikuti konfigurasi akun yang terlihat di `agy models`. CLI memakai effort tetap pada mode ini. Google melaporkan hasil mendekati Carbon, **19% lebih cepat** dan **24% lebih hemat kuota** pada pengujian internal. Blog Antigravity menyebut Terminal-Bench 4.1, sedangkan pengumuman Google tentang Hydrogen menyebut 4.0 untuk klaim yang sama. Perlakukan angka itu sebagai laporan Google untuk konfigurasi mereka. Saya tidak menemukan perbandingan publik yang menguji ketiga planner dengan kondisi seragam. [Pemilih model](https://antigravity.google/docs/models) · [Blog Antigravity](https://antigravity.google/blog/gemini-4-hydrogen-in-google-antigravity) · [Pengumuman Hydrogen](https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/).

## 8. Pilih per jenis pekerjaan

### Hydrogen untuk eksekusi cepat dan berulang

Pilih **Low** untuk ringkasan diff, regex, format teks, boilerplate pendek, atau daftar file yang perlu diperiksa. Pilih **Medium** untuk mengubah beberapa file dengan spesifikasi jelas. Gunakan **High** untuk debugging rutin, memperbaiki test, atau migrasi sederhana. Uji **xHigh** untuk pekerjaan agen yang dapat diverifikasi otomatis dan menuntut beberapa iterasi. Pada pengujian SWE Atlas, Hydrogen xHigh mengimbangi Carbon High pada penulisan test dan refactoring. Pengukuran Artificial Analysis menunjukkan berapa besar biaya dan waktu yang ditambahkan xHigh. [SWE Atlas Test Writing](https://labs.scale.com/leaderboard/swe-atlas?tab=testwriting) · [SWE Atlas Refactoring](https://labs.scale.com/leaderboard/swe-atlas?tab=refactoring) · [Artificial Analysis Hydrogen](https://artificialanalysis.ai/models/gemini-4-hydrogen).

### Neon untuk memahami kode, diagnosis, dan fitur yang ambigu

Pilih **High** jika Anda sudah tahu hasil yang diinginkan, tetapi belum tahu file yang harus diubah, penyebab error, atau kontrak internal yang dilanggar. Pilih **xHigh** untuk diagnosis dengan gejala yang mirip, alur lintas layanan, dan penelaahan patch yang membutuhkan pengecekan invarian. Neon memiliki QnA terkuat di antara empat model pada kedua pengujian CLI yang mencakup pemahaman repo. Di Artificial Analysis, Neon xHigh juga memiliki biaya dan waktu per tugas lebih rendah daripada Carbon High untuk suite coding. [Scale QnA](https://labs.scale.com/leaderboard/swe-atlas?tab=qna) · [Artificial Analysis Coding Agents](https://artificialanalysis.ai/agents/coding-agents/antigravity-cli).

### Carbon untuk pemecahan masalah terminal dan konteks panjang

Pilih **High** untuk build dan deployment internal yang rumit, masalah yang tergantung urutan kejadian, atau migrasi lintas repo dengan banyak dependensi. Minta model mengidentifikasi batas perubahan, hipotesis alternatif, dan verifikasi yang membedakan keduanya. Carbon mendapat skor resolusi tertinggi di antara empat model pada leaderboard penerbit Terminal-Bench 4.1 dan skor titik GraphWalks tertinggi di antara model yang melaporkan hasil untuk rentang 256K–1M. Jika pekerjaan terutama mencari jawaban di repo atau melakukan iterasi tanpa desain ulang, Neon atau Hydrogen punya bukti dan biaya yang lebih sesuai. [Terminal-Bench](https://www.tbench.ai/?efforts=all&version=4.1) · [Card Carbon](https://deepmind.google/models/model-cards/gemini-4-carbon/) · [Scale QnA](https://labs.scale.com/leaderboard/swe-atlas?tab=qna).

### Argon untuk kompatibilitas sementara

Jika masih punya workflow Argon, gunakan waktu transisi untuk membandingkan hasil yang penting bagi repo Anda. Ia menghasilkan skor titik yang baik untuk test writing dan refactoring di SWE Atlas, serta punya hasil SWE-Bench Pro V2 yang kuat pada protokol Scale. Pindahkan workflow reasoning ke Neon atau Carbon dan uji Hydrogen untuk pekerjaan yang spesifikasinya sudah mapan. Ketika workflow memakai Argon via API, ikuti lifecycle dan harga penyedianya. [Scale Test Writing](https://labs.scale.com/leaderboard/swe-atlas?tab=testwriting) · [Scale Pro V2](https://labs.scale.com/leaderboard/swe_bench_pro_public_v2) · [Model Antigravity](https://antigravity.google/docs/models) · [Lifecycle Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions).

### Peta tugas tambahan

| Tugas | Model dan effort awal | Ukuran sukses yang praktis |
| --- | --- | --- |
| CI gagal, satu log dan satu test reproduksi | Hydrogen High | Test yang gagal bisa direproduksi lalu lulus setelah patch |
| CI gagal intermiten, beberapa job atau platform | Neon xHigh, atau Carbon High untuk build system kompleks | Hipotesis dibedakan dengan bukti dari log dan reproduksi |
| Review PR atau patch buatan agen lain | Neon High | Temuan menunjuk file, baris, skenario kegagalan, dan test yang relevan |
| Menulis unit test untuk kontrak yang sudah didefinisikan | Hydrogen High atau xHigh | Test gagal untuk perilaku yang salah dan lolos untuk perilaku benar |
| API baru, model data baru, atau migrasi skema bertahap | Neon High untuk desain dan Carbon High untuk lintas layanan | Rencana kompatibilitas, rollback, dan validasi tiap tahap |
| Ratusan penggantian yang dapat diuji secara mekanis | Hydrogen Medium atau High | Diff berada dalam cakupan dan formatter, linter, serta test lulus |
| Menghasilkan UI dari brief visual longgar | Carbon High atau Neon xHigh | Alur browser utama bekerja, layout responsif, dan baseline aksesibilitas terpenuhi |
| Ringkasan log besar atau spesifikasi lintas dokumen | Neon High, atau Carbon High untuk hubungan yang tersebar | Setiap kesimpulan penting bisa ditelusuri ke artefak aslinya |
| Skrip batch untuk ekstraksi atau klasifikasi | Hydrogen Low, atau Flash-Lite jika biayanya lebih cocok di penyedia Anda | Validasi skema, akurasi sampel, dan biaya per item |
| Analisis matematika, data, atau algoritma yang sulit | Neon xHigh, atau Carbon High sebagai opsi kedua | Hasil dapat diperiksa melalui test, perhitungan, atau data acuan |

Pilihan di tabel merupakan titik awal. Skor Vals, Arena, Terminal-Bench, dan SWE Atlas mendukung beberapa pilihan tersebut melalui tugas yang berbeda. Metrik keberhasilan mengikuti hasil yang sebenarnya Anda butuhkan dari repo. [Vals Index](https://www.vals.ai/benchmarks/vals_index) · [WebDev Arena](https://arena.ai/leaderboard/code/webdev) · [Terminal-Bench 4.1](https://www.tbench.ai/?efforts=all&version=4.1) · [Scale SWE Atlas](https://labs.scale.com/leaderboard/swe-atlas?tab=overall).

## 9. Gemini 3 dan jalur lama yang masih relevan

Tabel ini memakai angka kartu model DeepMind. Kolom seri Terminal-Bench sengaja mencantumkan versi untuk setiap baris. Bandingkan hasil hanya bila suite, harness, dan protokolnya cocok. Kolom fungsi menunjukkan kegunaan praktis jika model tersebut tersedia pada jalur Anda.

| Model | Angka coding atau terminal yang dipublikasikan | Kapan masih berguna |
| --- | --- | --- |
| **Gemini 3.8 Flash** | DeepSWE v1.1 **73,7%** · Terminal-Bench 2.1 **89,4%** · 4.0 **19,1%** | Baseline Flash yang kuat untuk API atau workflow lama. Keluar dari Antigravity bersama Argon pada 30 Nov. Vals Index yang sama memberi 53,54% vs Hydrogen 67,07% |
| **Gemini 3.7 Flash** | DeepSWE v1.1 **65,3%** · Terminal-Bench 2.1 **85,8%** · 4.0 **11,2%** pada card 3.8 | Kompatibilitas Enterprise. Lifecycle Cloud menjadwalkan pensiun 28 Jan 2027 dan mengarahkan migrasi ke Hydrogen |
| **Gemini 3.6 Flash** | DeepSWE v1.1 **48,6%** pada card 3.7 · Terminal-Bench 2.1 **78,0%** · SWE-Bench Pro Public **58,7%** pada card 3.6 | Workflow Enterprise yang sudah dipatok dan punya test. Jadwal Cloud juga 28 Jan 2027 |
| **Gemini 3.5 Flash** | Terminal-Bench 2.1 **76,2%** dengan Terminus-2 · SWE-Bench Pro Public **55,1%** | Tier Flash pada konfigurasi Gemini CLI lama dan API yang mendukungnya |
| **Gemini 3.5 Flash-Lite** | Terminal-Bench 2.1 **54,0%** dengan Terminus-2 · SWE-Bench Pro Public **54,2%** | Batch terstruktur dengan validasi murah, ekstraksi, klasifikasi, atau asisten ringan |
| **Gemini 3.1 Pro** | Terminal-Bench 2.0 **68,5%** dengan Terminus-2 · SWE-Bench Verified **80,6%** | Reasoning pada akses Enterprise yang masih menawarkannya. Bandingkan Neon/Carbon ketika tersedia |
| **Gemini 3.1 Flash-Lite** | GPQA Diamond **86,9%** tanpa tool pada card. Angka ini mengukur pengetahuan ilmiah, sehingga tidak dipakai untuk menilai patch CLI | Tier Flash-Lite lama, parsing, dan batch sederhana |
| **Gemini 3 Pro** | Terminal-Bench 2.0 **56,9%** dengan Terminus-2 · SWE-Bench Verified **76,2%** sebagai baseline pada kartu 3.1 Pro | Reproduksi atau perbandingan workflow reasoning generasi lama |
| **Gemini 3 Flash** | SWE-Bench Verified **78,0%** menurut laporan peluncuran Google | Baseline Flash generasi lama apabila masih diaktifkan untuk jalur Anda |
| **Gemini 2.5 Pro / Flash / Flash-Lite** | Generasi lama dengan konfigurasi dan benchmark historis yang berbeda | Reproduksi workflow historis atau pemeliharaan integrasi lama. Google Cloud mencantumkan 20 Okt 2026 sebagai tanggal pensiun jalur Model Garden untuk tiga model 2.5 di tabel lifecycle |

Kartu model tersedia untuk [3.8 Flash](https://deepmind.google/models/model-cards/gemini-3-8-flash/) · [3.7 Flash](https://deepmind.google/models/model-cards/gemini-3-7-flash/) · [3.6 Flash](https://deepmind.google/models/model-cards/gemini-3-6-flash/) · [3.5 Flash](https://deepmind.google/models/model-cards/gemini-3-5-flash/) · [3.5 Flash-Lite](https://deepmind.google/models/model-cards/gemini-3-5-flash-lite/) · [3.1 Pro](https://deepmind.google/models/model-cards/gemini-3-1-pro/) · [3.1 Flash-Lite](https://deepmind.google/models/model-cards/gemini-3-1-flash-lite/). Hasil Gemini 3 Flash berasal dari [pengumuman Google](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-3-flash/).

Katalog dan status tersedia di [Model Antigravity](https://antigravity.google/docs/models) · [Lifecycle Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions) · [Kode katalog Gemini CLI](https://github.com/google-gemini/gemini-cli/blob/main/packages/core/src/config/models.ts) · [Pemilihan model Gemini CLI](https://geminicli.com/docs/cli/model/) · [Vals Index](https://www.vals.ai/benchmarks/vals_index).

Model Live, Omni, Nano Banana/image, dan Embedding tercantum sebagai keluarga dengan output atau fungsi khusus. Untuk script CLI, pertimbangkan mereka sebagai komponen tambahan untuk audio real-time, media, pembuatan gambar, atau pencarian semantik. Gunakan model reasoning untuk merencanakan perubahan dan menggunakan hasil komponen tersebut di repo. [Katalog Google Cloud](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models) · [Model cards DeepMind](https://deepmind.google/models/model-cards/).

## 10. Cara memakai di Antigravity CLI

Jalankan discovery melalui akun dan penyedia yang Anda pakai sebelum mematok slug. Di sesi interaktif gunakan `/model` dan `/effort`. Contoh headless di bawah memakai ID yang ditampilkan dokumentasi. [Referensi CLI](https://antigravity.google/docs/cli/reference) · [Headless](https://antigravity.google/docs/cli/headless/) · [Perintah effort](https://antigravity.google/docs/cli/commands/effort/).

```bash
agy --version
agy models

# Eksekusi ringan
agy --model gemini-4-hydrogen-low \
  -p 'Ringkas diff saat ini, file yang terdampak, dan test yang relevan.'

# Pemahaman codebase
agy --model gemini-4-neon-high \
  -p 'Telusuri alur checkout dari handler ke database. Sebutkan file dan fungsi kuncinya.'

# Diagnosis mendalam
agy --model gemini-4-neon-xhigh \
  -p 'Analisis log dan kode untuk kegagalan transaksi yang dijelaskan di issue lokal. Urutkan hipotesis berdasarkan bukti.'

# Perencanaan untuk tugas terminal yang kompleks
agy --model gemini-4-carbon-high \
  -p 'Petakan dependensi build, jelaskan risiko migrasi toolchain, dan susun langkah verifikasi.'

# Perencana Neon dengan eksekutor Hydrogen, jika tersedia di akun
agy --model 'Orchestrator (Neon)'
```

Untuk hasil yang bisa diproses program, dokumentasi menyediakan `--output-format json` dan `--output-format stream-json`. JSON cocok untuk hasil akhir. Stream JSON memberi event progres, tool call, dan statistik. Untuk menyelidiki konfigurasi aktif dalam mode headless, `agy -p "/effort" --output-format json` membaca konfigurasi. Atur effort per invokasi dengan slug berakhiran tingkat effort, atau flag `--effort` pada model yang mendukungnya. [Headless](https://antigravity.google/docs/cli/headless/) · [Perintah effort](https://antigravity.google/docs/cli/commands/effort/).

## 11. Uji banding singkat untuk repo Anda

Gunakan **Hydrogen Medium/High, Neon High/xHigh, dan Carbon High** sebagai konfigurasi kandidat. Tambahkan Orchestrator jika ingin mengetahui apakah pembagian perencana–eksekutor membantu. Contoh pengukuran berikut merupakan rancangan yang dapat dijalankan di lingkungan Anda.

1. Ambil **12 tugas representatif**. Contohnya tiga bug, tiga perubahan lintas file, tiga tugas menulis test, dua pertanyaan pemahaman repo, dan satu kegagalan build. Pakai tugas dengan kriteria yang sudah bisa dinilai.
2. Uji semua konfigurasi dari commit yang sama, dengan worktree atau salinan baru per run. Pakai prompt, versi CLI, autentikasi, akses tool, timeout, dependensi, dan budget yang sama sejauh memungkinkan.
3. Untuk putaran awal, bandingkan konfigurasi **High** pada semua model yang Anda gunakan. Putaran berikutnya menguji konfigurasi yang benar-benar akan dipakai, termasuk Hydrogen Medium, Neon xHigh, atau Orchestrator. Ulangi dua atau tiga kali per tugas jika anggaran memadai.
4. Nilai keluaran dengan test dan rubrik yang dikunci sebelum run. Hitung gagal karena timeout, error tool, patch berlebih, dan kebutuhan intervensi. Pertanyaan repo bisa dinilai dengan daftar fakta dan referensi file yang harus muncul.
5. Rekam persentase tugas selesai, median dan P90 durasi, token input/output/thinking/cache, percobaan ulang, dan **biaya per hasil yang lolos**. Lihat hasil per kategori. Jika Hydrogen lolos pada kategori rutin dan selisih kualitas pada kasus berat besar, jadikan Hydrogen default untuk pekerjaan rutin dan eskalasikan kasus berat sesuai kategori.

| Kolom log | Isi |
| --- | --- |
| `task_id, category, commit, run` | Identitas pekerjaan dan kondisi awal |
| `cli_version, provider, model, effort` | Kombinasi yang diuji |
| `pass, duration_s, interventions` | Hasil, durasi, dan intervensi manual |
| `input_tokens, cache_read_tokens, output_tokens, thinking_tokens` | Statistik sesuai semantik penyedia agar thinking dan cache tidak dihitung dua kali |
| `cost_usd, notes` | Tagihan atau perkiraan tarif, dan penyebab kegagalan |

**Biaya per hasil yang lolos** dihitung dari total biaya semua percobaan dibagi jumlah hasil yang lolos. Sebagai ilustrasi, $24 untuk 12 percobaan dan 8 hasil lolos menghasilkan $3 per hasil lolos. Catat jenis kegagalan untuk menilai biaya intervensi yang tak terlihat pada angka token. [Format statistik headless](https://antigravity.google/docs/cli/headless/) · [Tarif Developer API](https://ai.google.dev/gemini-api/docs/pricing).

## 12. Mengapa sumber bisa mengurutkan model secara berbeda?

| Pertanyaan | Bukti yang paling relevan | Batas interpretasi |
| --- | --- | --- |
| Agen mana yang paling sering menyelesaikan tugas terminal? | Terminal-Bench 4.1 dengan Antigravity CLI | Skor per run, interval yang bertumpang tindih, dan beberapa level effort |
| Model mana yang paling seimbang untuk pekerjaan engineering yang bermacam-macam? | Artificial Analysis Coding Agent Index dan Scale SWE Atlas | Komposisi tugas berbeda. Gunakan kategori yang paling mirip pekerjaan Anda |
| Mana yang cepat dan murah di endpoint? | Artificial Analysis model pages, harga API resmi | Latensi endpoint dan harga token dapat berubah. Harga per token hanya salah satu komponen biaya satu tugas |
| Mana yang paling bagus memahami repo atau membuat frontend? | Scale QnA dan Arena WebDev, masing-masing untuk tugasnya | Pemahaman repo berfokus pada jawaban yang dapat dinilai. Arena menangkap preferensi pengguna |
| Bagaimana kualitas untuk konteks besar, gambar, matematika, atau agen dokumen? | Model card DeepMind, Vals, dan evaluasi independen yang sesuai | Cocokkan versi benchmark, modalitas, effort, dan penggunaan alat sebelum membuat klaim lintas model |
| Bisakah saya memakai hasilnya untuk memilih model di CLI lain? | Benchmark CLI yang Anda pakai, atau run berpasangan di repo yang sama | Prompt, alat, context compaction, dan batas waktu dapat mengubah hasil |

Selisih kecil sebaiknya dianggap sebagai sinyal untuk pengujian lokal. Kesimpulan yang berulang di berbagai sumber adalah **Hydrogen paling menarik untuk pekerjaan berulang, Neon kuat untuk pemahaman repo, dan Carbon layak dipilih saat keberhasilan menyelesaikan tugas terminal rumit lebih penting daripada kecepatan atau biaya**. Bukti publik belum cukup untuk menetapkan satu urutan universal di semua effort dan CLI. [Terminal-Bench 4.1](https://www.tbench.ai/?efforts=all&version=4.1) · [Artificial Analysis](https://artificialanalysis.ai/agents/coding-agents/antigravity-cli) · [Scale SWE Atlas](https://labs.scale.com/leaderboard/swe-atlas?tab=overall) · [Vals Index](https://www.vals.ai/benchmarks/vals_index).
