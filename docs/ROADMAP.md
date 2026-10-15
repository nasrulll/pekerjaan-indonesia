# Roadmap RPI — keputusan arsitektur terkunci

## Riwayat rilis fondasi (hingga tag v0.4.0)

- **v0.1.0** — katalog awal 811 pekerjaan draf, 39 sektor editorial, klasifikasi 10 kelompok besar.
- **v0.2.0** — SQLite, PostgreSQL schema/loader, Git, CSV/JSON, API, CI.
- **v0.3.0** — nama berbahasa Indonesia; struktur jabatan, wilayah, pengupahan, kompetensi dan kelas gaji; API baca-saja berbahasa Indonesia; tanpa data resmi yang belum terverifikasi.
- **v0.4.0** — adapter/DDL/loader generik enam SQL (hanya SQLite diuji live), pencarian sinonim, struktur ISCO/ESCO/O_NET, endpoint analitik, contoh SDK enam bahasa, dashboard statis, sinkronisasi checksum paket lokal, Parquet opsional, kebijakan lisensi, kontribusi dan pengujian regresi.

## Pengembangan v0.5.0 — status terkini

Kode alat audit nasional sudah di-merge, tetapi dataset resmi tetap belum tersedia:

- **KBJI (#1):** validator manifest, audit kode/edisi/hierarki, dan calon pemetaan nama. [Panduan KBJI](ALUR_AUDIT_KBJI.md).
- **Wilayah (#2):** audit sistem kode dan edisi wilayah, jenis provinsi/kabupaten/kota serta induk. [Panduan wilayah](ALUR_AUDIT_WILAYAH.md).
- **UMP/UMK (#3):** audit keputusan, tanggal, nominal dan status revisi; bukan statistik rata-rata. [Panduan upah](ALUR_AUDIT_UPAH_MINIMUM.md).

Semua menggunakan data sintetis pada pengujian. **0 kode KBJI terverifikasi, 0 wilayah resmi terverifikasi, 0 data UMP/UMK terverifikasi**. Penambahan data resmi memerlukan izin redistribusi, sumber primer, pemeriksaan edisi, dan persetujuan manusia.

Repositori sudah dipublikasikan di GitHub; pada pengujian CI di 15 Oktober 2026, SQLite, PostgreSQL, dan MariaDB telah memiliki bukti integrasi. Ini tidak berarti siap produksi. MySQL langsung, SQL Server, dan Oracle belum memiliki pengujian server yang setara. Tag `v0.4.0` tetap terkunci dan tidak diubah.

## Kapabilitas yang sudah memiliki fondasi tetapi tetap menunggu hasil eksternal

- **v0.5.x — Data resmi tervalidasi:** verifikasi sumber KBJI, kode wilayah dan UMP/UMK; konektor instansi **belum tersedia**; tidak mengisi nilai palsu.
- **v0.6.x — API publik/SDK:** skema API ada; publikasi paket npm/PyPI/dll dan pengujian kompiler belum dilakukan.
- **v0.7.x — Analitik:** endpoint dan dashboard statis ada; agregasi statistik berkualitas nasional, DuckDB runtime dan grafik interaktif lebih lengkap menunggu sumber.
- **v0.8.x — Pencarian/klasifikasi:** sinonim/peringkat deterministik ada; NLP/AI dan pemetaan internasional terverifikasi belum ada. Pemetaan otomatis tidak boleh menjadi "kode resmi" tanpa reviewer.
- **v0.9.x — Audit pra-produksi:** unit test ada; pengujian integrasi database nyata selain SQLite, rate limiting, beban produksi, privasi dan penetration test menunggu lingkungan.
- **v1.0.0 — Rilis stabil:** baru bila semua gerbang verifikasi dalam `docs/KEAMANAN_KINERJA.md` terpenuhi. **Belum dirilis.**

Prinsip tetap: Git/CSV adalah sumber data induk; ID stabil dan edisi klasifikasi disimpan; hanya data bersumber jelas yang boleh dipublikasi; tidak menggabungkan gaji pokok, UMP/UMK, mean/median penghasilan dan perkiraan model.
