# Changelog

## v0.2.0 — 2026-10-15 — Multiplatform data + REST API

- Menambahkan FastAPI REST v1 berbasis SQLAlchemy, OpenAPI, health check, pencarian, filter, pagination, data sektor/jabatan/konteks, kode KBJI terverifikasi, serta ekspor JSON dan CSV.
- Menambahkan PostgreSQL UPSERT transaksional dengan `--apply` eksplisit, dan paritas kolom `alternative_names` pada skema.
- Memperkuat SQLite: build atomik, validasi FK, tabel alias relasional; mempertahankan dukungan pencarian CLI.
- Menambahkan builder snapshot SQLite/JSON/CSV dan manifest SHA-256; Dockerfile, Compose, contoh konfigurasi, dokumentasi dan tes API.
- Menjaga 811 entri tetap `draft`, dan mapping kode KBJI resmi tetap kosong sampai proses verifikasi.

## v0.1.0 — 2026-10-15 — Bootstrap awal

- Katalog kurasi 811 pekerjaan, 39 sektor editorial, 10 kelompok mayor KBJI.
- CSV + skema awal PostgreSQL + builder SQLite, JSON, validator, test, GitHub Actions.
