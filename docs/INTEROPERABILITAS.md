# Interoperabilitas basis data RPI v0.4.0

## Prinsip

- **Git/CSV** adalah master data dan riwayat review. Seluruh database adalah replika untuk baca atau layanan, **bukan** sumber kebenaran baru. ID pekerjaan/jabatan stabil lintas versi.
- SQLAlchemy menyediakan lapisan schema, parameter dan koneksi; **kompilasi DDL tidak sama dengan uji integrasi native**. Perbedaan collation, ukuran indeks, BLOB/CLOB, timezone, locks, dan batas panjang index harus dites pada server nyata.
- **SQLite**: snapshot offline diverifikasi; importer `impor_multibasis` sudah dites dengan SQLite dua kali.
- **PostgreSQL**: ada loader native lama dan loader generik; tidak ada live PostgreSQL yang tersedia pada sesi ini.
- **MySQL, MariaDB, SQL Server, Oracle**: dialect/DDL dan adapter sudah ada, tetapi migrasi native/loader dan API belum dibuktikan pada server riil. Jangan gunakan di produksi sebelum tes migrasi/upsert/pagination/rollback masing-masing.
- **DuckDB/Parquet**: ekspor Parquet opsional untuk analitik (bergantung `pyarrow`); bukan mesin transaksi kanonis. MongoDB dan TiDB belum didukung resmi karena butuh adapter dan pengujian terpisah. Supabase memakai PostgreSQL (butuh uji akses nyata).

## Driver / URL

| Sistem | Contoh URL (tanpa sandi sebenarnya) | Instalasi opsional |
|---|---|---|
| SQLite | `sqlite+pysqlite:////abs/rpi.db` | bawaaan Python |
| PostgreSQL | `postgresql+psycopg://pengguna:...@host/rpi` | `pip install -e '.[postgres]'` |
| MySQL | `mysql+pymysql://pengguna:...@host/rpi?charset=utf8mb4` | `pip install -e '.[mysql]'` |
| MariaDB | `mariadb+pymysql://pengguna:...@host/rpi?charset=utf8mb4` | `pip install -e '.[mysql]'` |
| SQL Server | `mssql+pyodbc://pengguna:...@host/rpi?driver=ODBC+Driver+18+for+SQL+Server` | `pip install -e '.[mssql]'` dan ODBC Driver |
| Oracle | `oracle+oracledb://pengguna:...@host:1521/?service_name=svc` | `pip install -e '.[oracle]'` |

Sandi dan konfigurasi harus melalui secret manager atau variabel lingkungan, bukan Git. HTTPS/TLS, role baca-saja, dan jaringan terisolasi wajib di lingkungan produksi. Gunakan database dengan UTF-8/Unicode.

## Instalasi database kosong

```bash
python scripts/validate.py
python scripts/impor_multibasis.py                          # dry run; tidak terkoneksi
RPI_DATABASE_URL=sqlite+pysqlite:////tmp/rpi.db python scripts/impor_multibasis.py --buat-skema --terapkan
RPI_DATABASE_URL=sqlite+pysqlite:////tmp/rpi.db python scripts/impor_multibasis.py --terapkan # idempoten
```

`--buat-skema` akan **menolak database yang sudah memiliki tabel**. Pada database yang sudah ada, lakukan migrasi eksplisit dan backup, uji staging, kemudian gunakan `--terapkan` tanpa `--buat-skema`. Perubahan pada record sumber bisa menimpa kolom yang sama di replika; record yang hilang dari Git **tidak** dihapus otomatis.

## Migrasi PostgreSQL yang telah memiliki RPI v0.3

```bash
psql "$POSTGRES_DSN" -v ON_ERROR_STOP=1 -f schema/postgresql_interoperabilitas.sql
RPI_DATABASE_URL="$POSTGRES_DSN" python scripts/impor_multibasis.py --terapkan
```

Untuk PostgreSQL baru gunakan `schema/postgresql.sql` atau `--buat-skema` pada database benar-benar kosong. Skema data dan riwayat tetap dilindungi versi Git; Alembic dapat dipakai untuk migrasi mendatang, tetapi **tidak ada migrasi otomatis universal yang dijamin aman** pada database yang berisi data.

## API

Endpoint baca-saja `GET /v1/...` dan `/openapi.json`; jalur v0.2 tetap tersedia. Pagination `LIMIT/OFFSET` dipetakan khusus untuk SQL Server/Oracle `OFFSET ... FETCH`. Akses publik sebaiknya melalui reverse proxy dengan TLS, rate limiting, autentikasi bila perlu, log audit yang tidak memuat data pribadi, dan backup berkala. Deployment dan uji beban produksi belum dilakukan.

## Alembic (installer baru, bukan upgrader otomatis)

Fondasi migrasi Alembic tersedia di `migrasi/` dengan revisi `20261015_0400` untuk **database kosong**, tanpa penghapusan otomatis. Instal `pip install -e '.[migrasi]'`, lalu set `RPI_DATABASE_URL` dan jalankan `alembic upgrade head`. Untuk upgrade dari database RPI v0.3 yang telah ada **jangan** menjalankan revisi awal pada data produksi; jalankan migrasi `schema/postgresql_interoperabilitas.sql` yang direview, uji backup/rollback, dan kelola penanda baseline Alembic secara terpisah. Versi baru perlu revisi migrasi eksplisit, jangan bergantung pada `create_all` untuk perubahan kolom.

## CI integrasi langsung yang disiapkan

`.github/workflows/integrasi-sql.yml` menyiapkan layanan PostgreSQL dan MariaDB, menjalankan impor dua kali, serta memanggil API langsung. **Workflow ini belum pernah berjalan pada GitHub**; hasil lulus untuk PostgreSQL/MariaDB tidak boleh diklaim sampai eksekusi CI berhasil. Pengujian native MySQL, SQL Server, Oracle dan server produksi tetap tugas terpisah.
