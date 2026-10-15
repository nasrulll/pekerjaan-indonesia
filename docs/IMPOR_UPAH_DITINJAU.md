# Impor kandidat UMP/UMK historis — RPI v0.5 (issue #3)

Status *ditinjau* tidak sama dengan "resmi terverifikasi". CSV input dan semua pengujian
dalam PR ini memakai data sintetis. **Belum ada angka upah pemerintah yang diimpor.**

## Persyaratan

- Jalankan migrasi database historis pada lingkungan yang sesuai dan pastikan
  \`wilayah_per_edisi\` telah diisi dengan wilayah berstatus ditinjau/terverifikasi.
- Buat CSV wilayah dari sistem dan edisi yang sudah di-review, menggunakan
  \`templates/wilayah_taksonomi_template.csv\`.
- Buat CSV keputusan sesuai \`templates/upah_minimum_keputusan_template.csv\`.
  Satu paket hanya boleh memuat satu sistem kode, satu edisi wilayah dan satu tahun.
- Manifest JSON \`jenis_sumber=upah_minimum\` dengan edisi sama dengan tahun,
  status \`menunggu_verifikasi\`, bukti izin distribusi dan SHA-256 dokumen primer.
- Dokumen primer tetap tersimpan di tempat yang sah, tidak diunggah otomatis ke Git.
- JSON persetujuan reviewer wajib berisi: \`sha256_csv_diolah\`,
  \`sha256_csv_wilayah\`, \`sha256_berkas_sumber\`, \`sistem_kode\`,
  \`edisi_wilayah\`, \`tahun\`, \`peninjau\`, \`tanggal_persetujuan\` (ISO)
  dan \`status=disetujui_untuk_impor_ditinjau\`.

## Eksekusi

\`\`\`bash
# Audit tanpa menulis ke database
python scripts/impor_upah_ditinjau.py \
  --csv-upah /path/keputusan.csv --csv-wilayah /path/wilayah.csv \
  --manifest /path/manifest.json --berkas-asli /path/keputusan-asli \
  --persetujuan /path/persetujuan.json

# Setelah memeriksa hasil dan menjalankan migrasi database dengan aman:
RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi-sudah-dimigrasi.sqlite3' \
python scripts/impor_upah_ditinjau.py \
  --csv-upah /path/keputusan.csv --csv-wilayah /path/wilayah.csv \
  --manifest /path/manifest.json --berkas-asli /path/keputusan-asli \
  --persetujuan /path/persetujuan.json --terapkan
\`\`\`

## Aturan keselamatan data

1. UMP hanya untuk provinsi; UMK hanya kabupaten/kota.
2. Semua wilayah dalam keputusan harus ada di database dengan edisi sama.
3. Keputusan pengganti mengacu ke nomor keputusan sebelumnya untuk
   wilayah, tahun, jenis, sistem dan edisi yang sama.
4. Dua keputusan berbeda berstatus \`berlaku\` dalam satu wilayah/tahun/jenis
   ditolak, termasuk antar-paket yang sudah masuk database.
5. Record identik dapat diimpor kembali; perubahan tidak akan menimpa diam-diam.
6. Semua hasil dimasukkan ke \`keputusan_upah_historis\` berstatus \`ditinjau\`.
   Tidak menulis ke tabel upah publik lama atau menerbitkan statistik resmi.

**Batasan:** metadata, checksum, dan persetujuan adalah pemeriksaan konsistensi,
bukan pembuktian otomatis keaslian instansi/putusan ataupun hak publikasi.
Setiap keputusan, perubahan keputusan, dan izin distribusi harus diperiksa manusia.
