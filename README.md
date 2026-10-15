# Pekerjaan Indonesia / NOR-ID

**Repositori open-data-ready untuk katalog pekerjaan Indonesia: Git + PostgreSQL + SQLite + REST API + JSON/CSV.**

![Version](https://img.shields.io/badge/version-0.2.0-blue)

> **Penting:** data v0.2.0 berisi **811 judul pekerjaan hasil kurasi dalam 39 sektor editorial**, seluruhnya `draft`. **Belum ada kode KBJI individu terverifikasi** dan repositori ini **bukan daftar resmi seluruh pekerjaan di Indonesia**. Cakupan lengkap harus direkonsiliasi dengan publikasi KBJI resmi dan sumber regulasi kompeten, dengan menghormati lisensi.

## Status implementasi

| Komponen | Kondisi |
|---|---|
| Master katalog Git/CSV, provenance & governance | Tersedia |
| PostgreSQL skema + loader UPSERT transaksional | Implementasi tersedia; uji DB riil masih diperlukan |
| SQLite offline, dibangun atomik | Teruji |
| REST API FastAPI + OpenAPI (read-only) | Teruji dengan SQLite |
| JSON/CSV + SHA-256 manifest | Teruji |
| Docker Compose PostgreSQL + seed + API | Konfigurasi tersedia; uji Docker riil masih diperlukan |
| KBJI resmi lengkap & verifikasi | Belum tersedia (0 mapping) |

## Diagram arsitektur

```text
Git / data/*.csv (sumber data kanonik; review & CI)
                 |
         scripts/validate.py
                 |
         +-------+-----------+
         |                   |
  build_release.py     load_postgres.py --apply
         |                   |
    SQLite+JSON+CSV      PostgreSQL produksi
         |                   |
         +-----> REST API <---+
                    |
         Web / Mobile / SKPGen / HRIS
```

## Instalasi cepat (lokal/offline)

Python 3.10+ diperlukan.

```bash
python -m pip install -e '.[server,test]'
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/build_release.py
python scripts/search.py 'guru'
uvicorn nor_id.api:app --host 127.0.0.1 --port 8000
```

Dokumentasi REST interaktif tersedia di `http://127.0.0.1:8000/docs` dan contoh pencarian pada `/v1/occupations?q=perawat`. Snapshot hasil build disimpan dalam `dist/` (diabaikan oleh Git).

## PostgreSQL + Docker

```bash
cp .env.example .env
# Ganti POSTGRES_PASSWORD dahulu
# Perlu Docker/Compose berjalan:
docker compose up --build -d
```

Docker API hanya diekspos pada `127.0.0.1:8000` untuk penggunaan lokal. Baca [panduan deployment](docs/DEPLOYMENT.md) sebelum mengaksesnya dari jaringan publik. Tanpa Docker gunakan `schema/postgresql.sql` dan `scripts/load_postgres.py` sesuai panduan.

## API tersedia

| Endpoint | Tujuan |
|---|---|
| `/v1/meta` | Status dataset dan kode resmi terverifikasi |
| `/v1/sectors` | Daftar sektor editorial |
| `/v1/occupations?q=...` | Pencarian, filter, pagination |
| `/v1/occupations/{id}` | Detail pekerjaan dan jabatan |
| `/v1/job-titles` | Jabatan organisasi |
| `/v1/employment-contexts` | Konteks kerja |
| `/v1/kbji/codes` | Kode dari mapping yang diverifikasi saja |
| `/v1/exports/occupations.json` | Unduh JSON |
| `/v1/exports/occupations.csv` | Unduh CSV |
| `/healthz`, `/docs`, `/openapi.json` | Health, Swagger, kontrak API |

[Lihat kontrak API lengkap](docs/API.md).

## Struktur repositori

```text
.github/workflows/ci.yml           # validasi dan artefak otomatis
nor_id/api.py                      # FastAPI read-only, SQLite/PostgreSQL
schema/postgresql.sql             # model relasional produksi
data/                             # CSV kanonik, sumber, referensi
scripts/build_sqlite.py           # SQLite offline atomik
scripts/load_postgres.py          # loader PostgreSQL transaksional
scripts/build_release.py          # snapshot CSV/JSON/SQLite + hash
scripts/validate.py               # validasi pekerjaan & kode KBJI
scripts/search.py                 # pencarian SQLite CLI
scripts/export_json.py            # JSON offline
tests/                            # test katalog dan integrasi API
docs/                             # panduan arsitektur dan integrasi
Dockerfile, compose.yml           # pengembangan berbasis kontainer
pyproject.toml                    # paket Python + dependensi opsional
```

## Prinsip data dan lisensi

Pekerjaan ≠ jabatan organisasi ≠ status kepegawaian ≠ bidang usaha. **KBJI** adalah klasifikasi pekerjaan; **KBLI** klasifikasi kegiatan usaha. `occupation_id` adalah identifier internal stabil, tidak sama dengan kode KBJI; kode KBJI hanya boleh ditambahkan dengan edisi, sumber, tanggal dan verifikator. Jangan mengklaim 39 sektor sebagai klasifikasi resmi. Proyek ini tidak memuat data pribadi, NIK, atau data kepegawaian individu.

Kode proyek berlisensi MIT. Data resmi eksternal hanya dapat diimpor dan didistribusikan sesuai hak/lisensi sumber masing-masing. Lihat [kebijakan sumber](docs/SOURCE_POLICY.md) dan [panduan kontribusi](CONTRIBUTING.md).

## Dokumen lain

- [Arsitektur multiplatform](docs/ARCHITECTURE.md)
- [Deployment / Docker / PostgreSQL](docs/DEPLOYMENT.md)
- [Integrasi SKPGen](docs/INTEGRATION_SKPGEN.md)
- [Kamus data](docs/DATA_DICTIONARY.md)
- [Roadmap](docs/ROADMAP.md)
- [Perubahan](CHANGELOG.md)

Repositori dibuat **secara lokal**; publikasi ke akun/organisasi GitHub tertentu memerlukan penentuan pemilik remote. Arsip Git Bundle dapat dikloning tanpa kehilangan commit.
