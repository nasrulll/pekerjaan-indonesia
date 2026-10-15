# Dokumentasi REST API v1

Swagger UI tersedia di `http://127.0.0.1:8000/docs`, dan OpenAPI JSON di `/openapi.json`.

## Menjalankan API dengan SQLite (development)

```bash
python -m pip install -e '.[server,test]'
python scripts/build_release.py
uvicorn nor_id.api:app --host 127.0.0.1 --port 8000
```

Jika menjalankan perintah dari lokasi lain, `NOR_DATABASE_URL` bisa menunjuk berkas SQLite:

```bash
export NOR_DATABASE_URL='sqlite+pysqlite:////full/path/pekerjaan-indonesia.sqlite3'
```

## Endpoint

| Method | Path | Fungsi |
|---|---|---|
| GET | `/healthz` | Koneksi database/health check |
| GET | `/v1/meta` | Ringkasan, status verifikasi |
| GET | `/v1/sectors` | 39 sektor editorial & jumlah pekerjaan |
| GET | `/v1/occupations` | Pencarian, filter, pagination |
| GET | `/v1/occupations/{occupation_id}` | Detail pekerjaan + jabatan |
| GET | `/v1/job-titles` | Daftar jabatan kurasi awal |
| GET | `/v1/employment-contexts` | Status/konteks kerja |
| GET | `/v1/kbji/codes` | Hanya kode KBJI dengan mapping sumber terverifikasi |
| GET | `/v1/exports/occupations.json` | Unduh seluruh katalog JSON |
| GET | `/v1/exports/occupations.csv` | Unduh seluruh katalog CSV UTF-8 (BOM untuk Excel) |

### Query dan status

`/v1/occupations` menerima `q` (maksimal 150 karakter), `sector_id` (mis. `SEC-005`), `status` (`draft`, `reviewed`, `published`, `archived`), `limit` (1..100, default 25), `offset` (>=0). `/v1/job-titles` menerima `q`, `occupation_id`, `limit`, `offset`. `/v1/kbji/codes` menerima `edition`, `limit`, `offset`.

```bash
curl 'http://127.0.0.1:8000/v1/occupations?q=perawat&limit=10'
curl 'http://127.0.0.1:8000/v1/occupations/ID-OCC-000135'
curl 'http://127.0.0.1:8000/v1/sectors'
```

### Contoh response ringkas

```json
{
  "data": [
    {
      "occupation_id": "ID-OCC-000135",
      "preferred_name_id": "Perawat",
      "record_status": "draft",
      "kbji_mappings": []
    }
  ],
  "pagination": { "total": 1, "limit": 10, "offset": 0, "has_more": false },
  "notice": "Katalog kurasi; tidak merupakan klasifikasi resmi KBJI. Periksa status dan bukti pemetaan."
}
```

Respons asli mungkin mengandung kolom lain; contoh ini hanya ilustrasi ringkas. Selalu tampilkan `record_status` dan `notice` pada UI konsumen. Jangan menggunakan data draft untuk keputusan kepegawaian/izin profesi otomatis.

## Error dan compatibility

- `404` ID pekerjaan tidak ditemukan; `422` filter/pagination tidak valid; `503` gagal health check.
- Semua endpoint saat ini **read-only**. Tidak ada API untuk menulis data.
- Versi kontrak URL adalah `v1`, versi rilis proyek `v0.2.0`. Perubahan breaking harus memperbarui versi URL.
- Aplikasi Android/mobile dapat mengakses API secara langsung; aplikasi browser mengatur CORS melalui `NOR_CORS_ORIGINS`.
