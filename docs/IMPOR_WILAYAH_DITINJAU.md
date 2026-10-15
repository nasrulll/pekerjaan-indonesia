# Impor wilayah administratif berstatus ditinjau (issue #2)

Modul ini hanya menulis **calon data wilayah**, bukan kode resmi pemerintah. Seluruh hasil selalu diberi status `ditinjau` dan tidak dipublikasikan sebagai data resmi.

## Berkas prasyarat

- CSV berisi `sistem_kode,edisi,kode_wilayah,nama_wilayah,jenis_wilayah,kode_induk`; satu paket hanya satu sistem kode dan satu edisi. Awali kode sebagai teks untuk menjaga nol awal.
- Manifest sumber mengikuti struktur `templates/kbji_manifest_template.json`, dengan `jenis_sumber=kode_wilayah`, `edisi` yang sesuai, status `menunggu_verifikasi`, serta status dan rujukan izin redistribusi yang telah ditinjau.
- Berkas sumber asli untuk memverifikasi SHA-256.
- Persetujuan JSON berisi `sha256_csv_diolah`, `sha256_berkas_sumber`, `edisi`, `sistem_kode`, `peninjau`, `tanggal_persetujuan` (YYYY-MM-DD), dan `status=disetujui_untuk_impor_ditinjau`.

## Eksekusi

```bash
# Untuk database kosong yang telah bermigrasi; bukan perintah upgrade sembarang produksi
export RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi-wilayah.sqlite3'
alembic upgrade head

# Pra-audit (tanpa perubahan DB)
python scripts/impor_wilayah_ditinjau.py --csv /path/wilayah.csv \
  --manifest /path/manifest.json --berkas-asli /path/dokumen-asli \
  --persetujuan /path/persetujuan.json

# Impor atomik dan idempoten berstatus ditinjau
python scripts/impor_wilayah_ditinjau.py --csv /path/wilayah.csv \
  --manifest /path/manifest.json --berkas-asli /path/dokumen-asli \
  --persetujuan /path/persetujuan.json --terapkan
```

Tabel `wilayah_per_edisi` mempertahankan referensi sistem kode + edisi dan provinsi sebagai induk kabupaten/kota. Nilai kode dan nama dari paket yang sama tidak boleh ditimpa diam-diam. Validasi otomatis hanya memeriksa konsistensi metadata; **keaslian instansi penerbit, persetujuan dan izin harus dicek manusia**.

Belum ada daftar wilayah pemerintah yang diimpor. Keputusan UMP/UMK historis baru dapat dimuat sesudah wilayah rujukannya tersedia. Baseline `v0.4.0` tetap tidak diubah.
