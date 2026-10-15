# Gerbang integritas data nasional — RPI v0.5 (issue #1, #2, #3)

**Pemeriksaan read-only, bukan pengesahan data resmi.** Alat ini membaca status
`terverifikasi` pada tabel historis dan membandingkan asal sumber, bukti lisensi,
hierarki KBJI, wilayah dan keputusan UMP/UMK. Tidak ada proses yang mengubah
status data secara otomatis.

## Penggunaan

```bash
# Jalankan terhadap database RPI yang sudah memiliki migrasi Alembic 0600.
RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi.db' \
  python scripts/audit_kesiapan_nasional.py \
  --laporan /tmp/laporan-kesiapan.json

# Gate untuk rilis data publik; exit 2 bila belum ada entri terverifikasi:
RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi.db' \
  python scripts/audit_kesiapan_nasional.py --wajib-entri-terverifikasi
```

Laporan mengandung hitungan per status, daftar kesalahan berdasarkan ID teknis,
serta `publikasi_diizinkan_otomatis: false`. Tidak mengembalikan identitas
peninjau maupun nominal upah dalam ringkasan.

## Aturan utama

- Sumber berstatus terverifikasi harus memiliki izin redistribusi, checksum,
  identitas penerbit, serta jejak peninjauan.
- Taksonomi KBJI terverifikasi harus merujuk sumber/edisi sesuai dan memiliki
  hierarki induk yang sudah terverifikasi.
- Kabupaten/kota harus memiliki induk provinsi yang terverifikasi dalam sistem
  kode dan edisi yang sama.
- UMP harus merujuk provinsi, UMK merujuk kabupaten/kota terverifikasi.
  Keputusan yang digantikan harus valid pada wilayah, tahun, dan jenis upah sama.
- Tidak boleh ada beberapa keputusan berstatus berlaku untuk wilayah/tahun/jenis
  sama; rantai keputusan tidak boleh bercabang atau bersiklus.
- Bila belum ada data terverifikasi, keluaran `menunggu_dataset_resmi` bukan
  pernyataan bahwa data nol rupiah atau tidak ada pekerjaan di Indonesia.

## Batasan audit otomatis

Nilai `lolos_pemeriksaan_teknis_menunggu_otorisasi_manusia` **BUKAN**
sertifikat keaslian dari BPS atau pemerintah daerah. Database dapat berisi
metadata yang dibuat keliru atau dipalsukan. Reviewer harus mengecek sumber
primer, keputusan hukum, cakupan dokumen, lisensi, validitas substansi dan
mencatat persetujuan publikasi terpisah sebelum memberi status resmi.

Alat ini tidak mengimpor data pemerintah dan tidak mengubah tag `v0.4.0`.
