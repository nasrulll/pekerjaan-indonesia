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

## Pembaruan v0.3: rute berbahasa Indonesia

Rute lama di atas dipertahankan agar integrasi v0.2 tidak rusak. Nama baru tersedia pada `/v1/pekerjaan`, `/v1/pekerjaan/{id_pekerjaan}`, `/v1/jabatan`, `/v1/wilayah`, `/v1/upah-minimum`, `/v1/statistik-upah`, dan `/v1/status-registri`.

Parameter baru memakai nama Bahasa Indonesia (`nama`, `batas`, `mulai`, `tahun`, `kode_wilayah`, `sistem_kode`, `metrik`, `id_pekerjaan`). Kode rute API `/v1/pekerjaan` mengeluarkan `nama_pekerjaan`, `id_pekerjaan`, `id_sektor`, `status_data`. Endpoint pengupahan hanya menampilkan data **terverifikasi**, dengan `data_tersedia=false` jika kosong. Selalu bedakan UMP/UMK dari rata-rata/median upah, serta data resmi, survei dan estimasi.

Seluruh kontrak baru terlihat pada OpenAPI `/docs`. Lihat [panduan v0.3](PENGEMBANGAN_V03.md).

## Pengembangan v0.5: API historis dengan gerbang publikasi

Endpoint baca-saja terpisah untuk tabel berversi:

- \`GET /v1/kbji/terverifikasi\` — kode KBJI per edisi.
- \`GET /v1/wilayah-historis/terverifikasi\` — wilayah menurut sistem kode dan edisi.
- \`GET /v1/upah-minimum-historis/terverifikasi\` — keputusan UMP/UMK yang berlaku per tahun, bukan rata-rata upah.

**Secara bawaan semua endpoint baru tertutup dan mengembalikan daftar kosong.**
Aktivasi memerlukan persetujuan operator terhadap sumber yang telah
diperiksa di luar aplikasi serta pengaturan \`RPI_PUBLIKASI_HISTORIS=aktif\`
dan \`RPI_SUMBER_DISETUJUI_PUBLIK\`.
Status \`draf\`/\`ditinjau\` dan sumber beridentitas \`KANDIDAT-\` selalu
ditolak. Jangan gunakan konfigurasi aktivasi sebelum sumber resmi dan
hak penggunaan ulang dikonfirmasi secara independen.

Detail batasan, metadata, dan penggunaan: [API Historis Terverifikasi](API_HISTORIS_TERVERIFIKASI.md).
