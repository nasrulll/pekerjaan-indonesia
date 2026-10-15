# Registri Pekerjaan Indonesia (RPI)

**Repositori Git terbuka untuk pekerjaan, jabatan, wilayah administratif, dan data pengupahan Indonesia.**

**Versi 0.3.0** — PostgreSQL (produksi), SQLite (offline), REST API, CSV dan JSON. **Seluruh modul, tabel baru, bidang dan endpoint baru menggunakan penamaan Bahasa Indonesia.** Paket lama `nor_id`, tabel sumber awal (`occupations`, `job_titles`), variabel `NOR_*` serta API lama tetap dipertahankan sebagai lapisan kompatibilitas v0.2.0.

> **Peringatan tentang cakupan:** Dataset saat ini memiliki **811 pekerjaan kurasi/draf**, **39 sektor editorial**, **3 contoh jabatan draf**, dan **0 pemetaan kode KBJI yang telah diverifikasi**. Belum ada kode wilayah resmi maupun nominal UMP/UMK/statistik upah di master dataset. Ini **belum** merupakan katalog lengkap Indonesia atau sumber pengupahan resmi. Angka tahun atau gaji tidak boleh diciptakan sendiri.

## Modul

| Modul | Kemampuan | Status |
|---|---|---|
| Katalog Pekerjaan Nasional | Pencarian 811 pekerjaan dan sektor editorial | Tersedia, data masih draf |
| Katalog Jabatan Nasional | Relasi pekerjaan, jenjang, induk jabatan, dan konteks kerja | Struktur aktif; 3 contoh draf |
| Referensi Wilayah Administratif | Kode wilayah per sistem, provinsi, kabupaten dan kota | Struktur dan API aktif; data 0 |
| Statistik Pengupahan Daerah | UMP, UMK, rata-rata, median, cakupan, tahun, sumber | Struktur dan API aktif; data 0 |
| Kompetensi dan Jenjang Karier | Kompetensi jabatan, kategori, jenjang, dan kelas gaji | Struktur aktif; data 0 |
| Sinkronisasi Data Resmi | Validasi sumber, tanggal, verifikasi dan audit impor | Validasi tersedia; konektor otomatis belum dibuat |
| Analisis Pekerjaan dan Penghasilan | Keluaran untuk visualisasi lintas wilayah/tahun | Struktur/API tersedia; dashboard belum dibuat |

## Arsitektur singkat

```text
Git + CSV terkurasi (master)
        │
  Validasi dan review
        ├──────────→ PostgreSQL (produksi)
        ├──────────→ SQLite (offline)
        ├──────────→ JSON / CSV + SHA-256
        └──────────→ REST API / OpenAPI
                           │
                  Web / Mobile / SKPGen / HRIS
```

## Instalasi

Python 3.10+ diperlukan.

```bash
python -m pip install -e '.[server,test]'
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/build_release.py
uvicorn nor_id.api:app --host 127.0.0.1 --port 8000
```

Dokumentasi REST API tersedia di `http://127.0.0.1:8000/docs` jika server dijalankan. Nama modul dan endpoint baru menggunakan Bahasa Indonesia.

## Endpoint REST baru

| Endpoint | Fungsi |
|---|---|
| `GET /v1/status-registri` | Jumlah data yang terisi |
| `GET /v1/pekerjaan?nama=perawat` | Pencarian pekerjaan; keluaran Bahasa Indonesia |
| `GET /v1/pekerjaan/{id_pekerjaan}` | Detail pekerjaan |
| `GET /v1/jabatan?nama=kepala` | Katalog dan hierarki jabatan |
| `GET /v1/wilayah?jenis_wilayah=provinsi` | Wilayah yang sudah terverifikasi |
| `GET /v1/upah-minimum?tahun=2026` | UMP/UMK terverifikasi |
| `GET /v1/statistik-upah?tahun=2026` | Statistik upah terverifikasi |

Endpoint v0.2 tetap berjalan, seperti `/v1/occupations`, `/v1/job-titles`, `/v1/meta` dan `/v1/exports/occupations.json`.

**Nilai kosong tidak diganti nol.** Jika statistik belum tersedia API mengembalikan daftar kosong dengan penanda `data_tersedia=false`; daftar contoh dalam pengujian tidak masuk master dataset.

## Migrasi PostgreSQL

**Database baru:** berkas `schema/postgresql.sql` mencakup tabel v0.2 dan tabel tambahan v0.3.

**Database v0.2 yang sudah ada:** jalankan `schema/postgresql_tambahan.sql` sekali pada PostgreSQL sebelum memakai loader v0.3. SQL dirancang idempoten, tanpa menghapus data v0.2. Jangan mengandalkan volume Docker lama menjalankan skrip init otomatis.

```bash
# Untuk PostgreSQL yang sudah disiapkan:
psql "$POSTGRES_DSN" -v ON_ERROR_STOP=1 -f schema/postgresql_tambahan.sql
RPI_DATABASE_URL="$POSTGRES_DSN" python scripts/load_postgres.py --apply
```

`RPI_DATABASE_URL` dipakai oleh API/Compose; `NOR_DATABASE_URL` lama masih diterima. Loader membutuhkan PostgreSQL dengan skema terpasang dan `psycopg`, serta **belum diuji terhadap server PostgreSQL riil dalam sesi ini**.

## Data dan bukti

- KBJI = klasifikasi pekerjaan; jabatan ASN = nomenklatur jabatan; KBLI = kegiatan usaha. Jangan dicampur.
- Kode wilayah harus mencantumkan sistem kodenya (misalnya BPS/Kemendagri), tahun/edisi, sumber, dan status verifikasi; kode disimpan sebagai teks.
- UMP/UMK **bukan** rata-rata atau median upah. Sumber, satuan, cakupan, jumlah sampel bila tersedia, dan periode wajib jelas.
- Data `resmi`, `survei`, dan `estimasi` dipisahkan. Data draf tidak keluar melalui endpoint pengupahan publik.
- Repository ini tidak menyimpan informasi gaji per orang, NIK, atau data pribadi.

Dokumentasi: [pengembangan dan kamus data v0.3](docs/PENGEMBANGAN_V03.md) · [ketentuan sumber](docs/SOURCE_POLICY.md) · [arsitektur v0.2 dan kompatibilitas](docs/ARCHITECTURE.md) · [API lama](docs/API.md).

Repo Git dibuat lokal. Publikasi GitHub dan deploy produksi membutuhkan pemilik remote serta lingkungan yang disetujui.
