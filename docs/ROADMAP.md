# Roadmap Pekerjaan Indonesia

## P0 — Fondasi Git (v0.1.0, selesai)

- [x] 811 judul pekerjaan awal, 39 sektor editorial, 10 kelompok mayor KBJI
- [x] CSV master, ID stabil, kamus data, kebijakan sumber, validasi dan CI
- [x] Skema PostgreSQL awal, SQLite lokal dan ekspor JSON

## P1 — Multiplatform (v0.2.0, implementasi tersedia)

- [x] REST API baca-saja (`/v1/occupations`, detail, sektor, jabatan, konteks, KBJI verified only)
- [x] SQLite offline, JSON/CSV, manifest checksum dan release builder
- [x] PostgreSQL upsert loader, Docker Compose, dokumen deployment
- [x] API test SQLite otomatis dan dukungan OpenAPI
- [ ] Jalankan end-to-end PostgreSQL + Docker pada server nyata, integrasikan ke CI
- [ ] Pengelolaan akun reviewer/editor dan migrasi skema produksi berurutan
- [ ] Penanganan data usang saat penghapusan di Git, snapshot version provenance

## P2 — Sinkronisasi sumber KBJI resmi (belum dikerjakan)

- [ ] Verifikasi edisi KBJI, izin distribusi, dan sumber pemerintah terkini
- [ ] Impor kode, nama, deskripsi dan hierarki yang boleh didistribusikan
- [ ] Rekonsiliasi judul awal dan mapping resmi dengan reviewer manusia
- [ ] Perhitungan kelengkapan per kelompok dan daftar konflik/duplikat

## P3 — Nomenklatur ASN dan profesi (belum dikerjakan)

- [ ] Jabatan struktural, fungsional, pelaksana ASN dan sumber regulasi
- [ ] Spesialisasi, subspesialisasi, lisensi profesi, sinonim dan riwayat perubahan
- [ ] Sistem sinkronisasi untuk HRIS/SKPGen, mapping regulasi yang diaudit

## P4 — Skala dan pengalaman (belum dikerjakan)

- [ ] Fuzzy search, autocomplete, multilanguage, ranking dan indeks produksi
- [ ] Versi dataset dan webhook/snapshot untuk konsumen API
- [ ] Rate limits di gateway, observability, API keys jika diperlukan

**Definisi selesai untuk klaim `seluruh pekerjaan`:** audit seluruh klasifikasi pada edisi KBJI rujukan dan rekonsiliasi nomenklatur lokal bersumber, bukan sekadar jumlah entri.
