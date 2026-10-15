# Registri Pekerjaan Indonesia (RPI)

**RPI v0.4.0 — Katalog pekerjaan, jabatan, wilayah, pengupahan dan interoperabilitas basis data.** Repositori Git terbuka dengan data kurasi awal dan API baca-saja berbahasa Indonesia; **bukan** database seluruh pekerjaan resmi dan bukan penyedia angka gaji resmi yang sudah lengkap.

> **Cakupan jujur saat ini:** **811 judul pekerjaan kurasi draf** pada **39 sektor editorial**, **10 kelompok besar KBJI sebagai referensi klasifikasi**, **3 jabatan contoh berstatus draf**. **0 pemetaan kode KBJI resmi tervalidasi**, **0 wilayah administratif terverifikasi**, **0 data UMP/UMK**, **0 statistik upah**, **0 pemetaan internasional terverifikasi**. Tidak ada angka imajiner. Nama sektor bukan kode KBLI dan jabatan bukan KBJI.

## Modul

1. **Katalog Pekerjaan Nasional** — judul/alias/identitas stabil, pencarian, API.
2. **Katalog Jabatan Nasional** — hierarki, jenis jabatan, konteks kerja, relasi KBJI.
3. **Referensi Wilayah Administratif** — sistem kode wilayah dan histori edisi lewat Git.
4. **Statistik Pengupahan Daerah** — UMP/UMK, statistik rata-rata/median terpisah.
5. **Kompetensi dan Jenjang Karier** — kompetensi, kelas gaji, kualifikasi (skema siap).
6. **Sinkronisasi dan Validasi Data** — checksum, paket tersertifikasi, review PR, riwayat Git.
7. **Analisis Pekerjaan dan Penghasilan** — endpoint ringkasan yang hanya membaca data terverifikasi dan dashboard statis.
8. **Interoperabilitas** — pemetaan internasional ISCO/ESCO/O*NET berbukti (struktur tersedia, data belum diisi).

## Status teknis dan batasan

| Teknologi | Implementasi | Status pengujian |
|---|---|---|
| PostgreSQL | Skema, loader native lama & generik | Kompilasi DDL; **belum diuji live v0.4** |
| SQLite | Skema, loader, snapshot offline | **Teruji**, termasuk idempoten dan foreign key |
| MySQL | Adapter SQLAlchemy/DDL/loader generik | Kompilasi DDL saja, **belum live** |
| MariaDB | Adapter SQLAlchemy/DDL/loader generik | Kompilasi DDL saja, **belum live** |
| Microsoft SQL Server | Adapter SQLAlchemy/ODBC, pagination | Kompilasi DDL/pagination, **belum live** |
| Oracle | Adapter SQLAlchemy/oracledb, pagination | Kompilasi DDL/pagination, **belum live** |
| REST API + OpenAPI | Endpoint Bahasa Indonesia + alias lama | **Teruji pada SQLite** |
| CSV, JSON, SQLite snapshot & SHA-256 | Paket rilis reproducible | **Teruji** |
| Parquet/DuckDB | Skrip ekspor Parquet opsional | **Belum diuji runtime** (pyarrow/duckdb belum ada) |
| Dashboard dan SDK | Dashboard statis, contoh 6 bahasa | Dashboard **belum browser diuji**; TypeScript/PHP/Java lolos sintaks/kompilasi lokal; .NET/Dart belum diuji |

**Tidak ada deployment produksi atau konektor resmi BPS/Kemnaker yang terpasang.** Nama adapter tidak berarti sudah sertifikasi produksi.

## Mulai dalam 3 langkah (lokal)

```bash
python -m pip install -e '.[server,test]'
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/build_release.py
uvicorn nor_id.api:app --host 127.0.0.1 --port 8000
```

Dokumentasi OpenAPI: `http://127.0.0.1:8000/docs` atau `/openapi.json`.

Contoh URL API:

```text
GET /v1/status-registri
GET /v1/pekerjaan?nama=perawat
GET /v1/jabatan?nama=kepala
GET /v1/cari-pekerjaan?kata=guru
GET /v1/wilayah?jenis_wilayah=provinsi
GET /v1/upah-minimum?tahun=2026
GET /v1/statistik-upah?tahun=2026
GET /v1/analisis/pengupahan?tahun=2026
GET /v1/pemetaan-internasional?sistem_klasifikasi=ISCO
```

Jalur API lama `/v1/occupations`, `/v1/job-titles`, dan `/v1/exports/occupations.json` tetap ada demi kompatibilitas v0.2.0. Paket internal Python `nor_id` dipertahankan sebagai nama teknis lama; nama publik tetap RPI.

## Migrasi & impor SQL multiplatform

```bash
python scripts/impor_multibasis.py                  # dry-run, tidak ada perubahan
# HANYA pada database kosong:
RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi.sqlite3' python scripts/impor_multibasis.py --buat-skema --terapkan
# Pembaruan idempoten; database harus sudah dimigrasikan:
RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi.sqlite3' python scripts/impor_multibasis.py --terapkan
```

Untuk engine lain, instal driver opsional dan isi `RPI_DATABASE_URL`. Jangan masukkan kredensial ke Git. **Jangan gunakan `--buat-skema` pada database produksi yang telah berisi tabel.** Cara migrasi PostgreSQL v0.3: `schema/postgresql_interoperabilitas.sql`. Tersedia pratinjau DDL lintas enam dialek di `schema/ddl/` dan migrasi Alembic hanya untuk database baru di `migrasi/`. Penjelasan detail: [interoperabilitas](docs/INTEROPERABILITAS.md).

## Rilis dan pembaruan dataset

`python scripts/build_release.py` membuat snapshot SQLite, CSV/JSON dan `dist/manifest.json` dengan checksum SHA-256. `python scripts/ekspor_parquet.py` membutuhkan `pyarrow` opsional. Mekanisme paket resmi lokal: [penyegaran data](docs/PENYEGARAN_DATA.md); uji checksum, skema, dan relasi sebelum review manusia dan merge PR.

Data resmi eksternal belum diunduh, sehingga tidak ada klaim cakupan seluruh wilayah atau UMP/UMK. Anda dapat mengajukan usulan sumber dan pekerjaan melalui [panduan kontribusi](CONTRIBUTING.md) dengan mempertahankan ID stabil. Pertimbangkan hak cipta dan privasi sebelum menambahkan data pihak lain.

## Dokumen proyek

- [Interoperabilitas enam basis data](docs/INTEROPERABILITAS.md)
- [Sinkronisasi dan verifikasi sumber](docs/PENYEGARAN_DATA.md)
- [Keamanan, kualitas dan kinerja](docs/KEAMANAN_KINERJA.md)
- [Lisensi dan hak redistribusi](DATA_LICENSE.md)
- [Kebijakan sumber data](docs/SOURCE_POLICY.md)
- [Contoh SDK berbagai bahasa](sdk/README.md)
- [Dashboard statis](dashboard/index.html)
- [Roadmap menuju rilis stabil](docs/ROADMAP.md)

**Penguncian:** v0.3.0 dipertahankan pada tag Git; v0.4.0 menjadi baseline baru setelah pengujian. Repo masih lokal, belum dipublikasikan ke GitHub karena pemilik remote belum ditentukan. RPI v1.0 hanya boleh diumumkan setelah kriteria verifikasi data dan integrasi produksi terpenuhi.
