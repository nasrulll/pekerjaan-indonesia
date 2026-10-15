# Cara menjalankan dan menyebarkan NOR-ID

## Opsi A — SQLite untuk demo/offline

```bash
python -m pip install -e '.[server,test]'
python scripts/build_release.py
uvicorn nor_id.api:app --host 127.0.0.1 --port 8000
```

Buka `http://127.0.0.1:8000/docs` dan tes `/healthz`, `/v1/meta`.

## Opsi B — PostgreSQL manual

1. Siapkan PostgreSQL 16+ dan basis data `norid`; gunakan kredensial yang tersimpan di secret manager atau environment lokal, bukan Git.
2. Inisialisasi skema melalui psql **sebelum** loader:

```bash
psql 'postgresql://USER:PASSWORD@HOST:5432/norid' -v ON_ERROR_STOP=1 -f schema/postgresql.sql
```

3. Jalankan validasi dan loader:

```bash
python -m pip install -e '.[server,postgres]'
python scripts/validate.py
export NOR_DATABASE_URL='postgresql+psycopg://USER:PASSWORD@HOST:5432/norid'
python scripts/load_postgres.py           # Dry-run: hanya validasi
python scripts/load_postgres.py --apply   # UPSERT transaksi eksplisit
uvicorn nor_id.api:app --host 127.0.0.1 --port 8000
```

4. Gunakan role database **baca-saja** berbeda untuk API; loader menggunakan role penulis hanya saat seed/migrasi. Terapkan TLS + proxy/limit akses untuk publik. Password yang mengandung `@`, `:` atau simbol URL lain wajib di-percent-encode.

## Opsi C — Docker Compose (pengembangan)

```bash
cp .env.example .env
# Isi POSTGRES_PASSWORD yang kuat dan aman untuk URI
# Sesudah itu:
docker compose up --build -d
curl http://127.0.0.1:8000/v1/meta
```

Compose menggunakan PostgreSQL 16, memuat skema pada **database kosong pertama kali**, melakukan seed UPSERT, dan menyediakan API di `127.0.0.1:8000`. Jika volume PostgreSQL sudah ada, skrip init tidak akan dijalankan ulang; jalankan migrasi skema secara eksplisit sebelum seeding. Jangan mengekspos port ini tanpa HTTPS, kontrol akses, backup dan rate limiting.

## Pembaruan data

Ubah sumber Git CSV melalui Pull Request, verifikasi provenance dan lisensi, jalankan test, keluarkan snapshot baru `python scripts/build_release.py`. Jika menggunakan PostgreSQL, cek perubahan skema dan data usang sebelum jalankan `--apply`; operasi ini **tidak menghapus record yang hilang dari Git**. Uji endpoint kontrak dan proses rollback sebelum deploy.

### Checklist produksi

- [ ] Migrasi skema dan seed diuji dengan instance PostgreSQL nyata
- [ ] Database role API hanya `SELECT`
- [ ] Backup/restore DB dan rollback snapshot diuji
- [ ] TLS/reverse proxy, rate limit, firewall dan pembatasan CORS
- [ ] Audit perubahan data resmi melalui PR
- [ ] Log, alert, performance baseline dan health check
