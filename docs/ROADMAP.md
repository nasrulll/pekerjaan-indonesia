# Roadmap Pengembangan

## P0 — Fondasi repositori (tersedia di v0.1.0)

- [x] Taksonomi 39 sektor editorial
- [x] 811 judul pekerjaan kurasi awal
- [x] Kamus data dan model PostgreSQL
- [x] Validasi CSV, pengujian, dan GitHub Actions
- [x] Ekspor JSON, pencarian SQLite lokal
- [x] Kebijakan provenance dan mencegah kode KBJI palsu

## P1 — Sinkronisasi sumber resmi (belum dikerjakan)

- [ ] Identifikasi edisi KBJI resmi terbaru, izin distribusi, dan salinan sumber
- [ ] Impor seluruh kode, nama, deskripsi dan tingkatan klasifikasi **yang diizinkan**
- [ ] Rekonsiliasi 811 nama awal vs kode KBJI
- [ ] Review silang minimal dua pemeriksa untuk mapping ambigu
- [ ] Persentase kelengkapan per kelompok mayor dan kode sumber
- [ ] Dokumentasi istilah yang tidak terpetakan/duplikat

## P2 — Jabatan dan spesialisasi (belum dikerjakan)

- [ ] Jabatan struktural, fungsional, pelaksana ASN dengan sumber/edisi regulasi
- [ ] Profesi spesialis/subspesialis serta izin/sertifikasi yang dipersyaratkan
- [ ] Pekerjaan formal, informal, dan lintas sektor
- [ ] Sinonim, nomenklatur regional, multibahasa
- [ ] Riwayat perubahan nama dan kode

## P3 — API dan integrasi (belum dikerjakan)

- [ ] API `/v1/occupations`, `/v1/occupations/{id}`, `/v1/kbji/codes`, `/v1/job-titles`
- [ ] Fuzzy search, autocomplete, indeks Bahasa Indonesia
- [ ] Hak akses admin/editor/reviewer; event audit log
- [ ] Snapshot dataset dan semantic versioning
- [ ] PostgreSQL ingestion otomatis dan migrasi

## P4 — Aplikasi penggunaan (belum dikerjakan)

- [ ] SKPGen AI: jabatan → contoh RHK/indikator berbasis regulasi yang diverifikasi
- [ ] Referensi data untuk HRIS, lowongan kerja, career guidance
- [ ] API kompatibel untuk sinkronisasi pihak ketiga

## Definisi selesai untuk tujuan `seluruh pekerjaan`

**Bukan jumlah absolut sewenang-wenang.** Cakupan penuh dinilai berdasarkan audit terhadap seluruh unit dan hierarki KBJI edisi rujukan yang ditetapkan, kesesuaian kode-label, serta daftar profesi lokal/spesialisasi yang punya sumber pendukung. Sebelum terpenuhi, gunakan istilah *katalog dalam pengembangan*.
