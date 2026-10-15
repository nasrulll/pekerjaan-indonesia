# Skema historis wilayah dan upah minimum — RPI v0.5.0

## Tujuan dan alasan

Fondasi RPI v0.4 memakai `wilayah_administratif(sistem_kode,kode_wilayah)` dan
`upah_minimum(sistem_kode,kode_wilayah,tahun,jenis_upah)`.
Struktur lama **tidak** cukup untuk menyimpan kode wilayah yang dipakai ulang
pada edisi berbeda, maupun lebih dari satu keputusan UMP/UMK pada satu periode.

RPI v0.5 menambahkan **tiga tabel historis tanpa mengganti tabel lama**:

| Tabel | Identitas | Tujuan |
|---|---|---|
| `sumber_publikasi` | `id_sumber` | Penerbit, edisi, SHA-256 asli, URL dan status persetujuan |
| `wilayah_per_edisi` | `(sistem_kode,edisi,kode_wilayah)` | Kode wilayah menurut sistem dan edisi, beserta hierarki |
| `keputusan_upah_historis` | `id_keputusan` | Nominal, tahun, nomor, tanggal, status keputusan serta relasi pengganti |

Skema mencakup foreign key, indeks lokasi/tahun, constraint nominal positif,
status verifikasi, tipe upah, dan keunikan identitas keputusan.

## Migrasi

### Untuk instalasi baru (belum ada data)

Pasang ekstra `migrasi` dan gunakan Alembic ke `head`:

```bash
python -m pip install -e '.[migrasi]'
# SQLite contoh untuk instalasi BARU saja
RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi-historis-baru.sqlite3' \
  alembic upgrade head
```

### Database v0.4 yang sudah ada

**Jangan** menjalankan migrasi awal `20261015_0400` lagi pada database
yang terisi. Buat backup, audit skema dan status Alembic dahulu.
Migrasi `20261015_0500` menambahkan tabel secara aditif, tetapi perlu
rencana `stamp`/upgrade yang ditinjau untuk database yang tidak memakai Alembic
sejak awal. Jangan melakukan `alembic stamp` tanpa memastikan kesetaraan skema.

Untuk menguji DDL secara lokal tanpa mengimpor data resmi:

```bash
python -m unittest tests.test_skema_histori -v
```

## Batasan dan pekerjaan berikutnya

- **Tidak ada data pemerintah baru** yang dimasukkan oleh migrasi ini.
- Tabel lama dan REST API v0.4 tetap tersedia; API yang membaca tabel
  baru memerlukan perluasan kontrak/versi dan pembatasan data verifikasi.
- Penetapan edisi, keaslian publikasi, izin redistribusi, validitas keputusan,
  kesesuaian status `berlaku` dan penggantinya **tidak dapat dijamin oleh
  constraint SQL saja**; harus diperiksa sebelum publikasi.
- Proses penyalinan (backfill) data historis dari tabel lama **tidak otomatis**.
  Di masa depan hanya data bersumber yang boleh ditransfer.
- Validasi sekarang masih memeriksa format kandidat di
  [audit wilayah](ALUR_AUDIT_WILAYAH.md) dan
  [audit upah](ALUR_AUDIT_UPAH_MINIMUM.md).

Terkait [issue #2](https://github.com/nasrulll/pekerjaan-indonesia/issues/2)
dan [issue #3](https://github.com/nasrulll/pekerjaan-indonesia/issues/3).
