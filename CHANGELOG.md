# Riwayat Perubahan

## 0.3.0 — 15 Oktober 2026

- Nama baru dalam Bahasa Indonesia: **Registri Pekerjaan Indonesia (RPI)**, dengan kompatibilitas NOR-ID v0.2.0.
- Tabel baru: jabatan nasional, wilayah administratif, pemetaan jabatan KBJI, kompetensi jabatan, upah minimum, statistik upah, kelas gaji, dan riwayat impor.
- API Bahasa Indonesia: status registri, pekerjaan, jabatan, wilayah, upah minimum, statistik upah. API Inggris lama tidak dihapus.
- Validasi data sumber, kode wilayah berhierarki, UMP/UMK sesuai level wilayah, satuan/statistik, dan bukti verifikasi.
- Ekspor CSV/JSON lokal berbahasa Indonesia, snapshot SQLite, manifest checksum, dan PostgreSQL skema serta loader.
- Tidak menambahkan angka upah atau kode KBJI/wilayah yang tidak memiliki verifikasi sumber.
- Docker/PostgreSQL tersedia sebagai konfigurasi; uji DB nyata dan publikasi GitHub belum dilakukan.

## v0.2.0 — 2026-10-15 — Multiplatform data + REST API

- Menambahkan FastAPI REST v1 berbasis SQLAlchemy, OpenAPI, health check, pencarian, filter, pagination, data sektor/jabatan/konteks, kode KBJI terverifikasi, serta ekspor JSON dan CSV.
- Menambahkan PostgreSQL UPSERT transaksional dengan `--apply` eksplisit, dan paritas kolom `alternative_names` pada skema.
- Memperkuat SQLite: build atomik, validasi FK, tabel alias relasional; mempertahankan dukungan pencarian CLI.
- Menambahkan builder snapshot SQLite/JSON/CSV dan manifest SHA-256; Dockerfile, Compose, contoh konfigurasi, dokumentasi dan tes API.
- Menjaga 811 entri tetap `draft`, dan mapping kode KBJI resmi tetap kosong sampai proses verifikasi.

## v0.1.0 — 2026-10-15 — Bootstrap awal

- Katalog kurasi 811 pekerjaan, 39 sektor editorial, 10 kelompok mayor KBJI.
- CSV + skema awal PostgreSQL + builder SQLite, JSON, validator, test, GitHub Actions.
