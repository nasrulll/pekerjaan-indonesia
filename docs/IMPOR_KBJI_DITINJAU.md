# Impor KBJI berstatus ditinjau — RPI v0.5 (issue #1)

Modul ini menerima taksonomi KBJI **kandidat** yang telah diperiksa manusia,
merekam identitas sumber, edisi, hierarki dan checksum; ia **tidak mengesahkan**
KBJI resmi atau memublikasikan pemetaan pekerjaan.

## Persiapan paket

Siapkan empat berkas **di luar repositori publik**:

1. Taksonomi CSV UTF-8: \`edisi,kode,nama,kode_induk,tingkat\`. Semua kode harus string agar nol awal tetap utuh.
2. Manifest JSON menurut \`templates/kbji_manifest_template.json\`; \`jenis_sumber=klasifikasi_kbji\`, \`izin_distribusi=diizinkan\`, \`rujukan_izin\` dan \`sha256_berkas_sumber\` wajib ada. Status manifest masih \`menunggu_verifikasi\`.
3. Berkas asli yang checksum SHA-256-nya dicatat di manifest (tidak otomatis diunggah ke Git).
4. JSON persetujuan manusia dengan \`peninjau\`, \`tanggal_persetujuan\` (ISO),
\`edisi\`, \`sha256_csv_diolah\`, \`sha256_berkas_sumber\`, dan
\`status=disetujui_untuk_impor_ditinjau\`.

Pemeriksaan ini memvalidasi struktur dan konsistensi bukti; identitas reviewer,
domain penerbit, dan izin tidak dapat dibuktikan hanya dengan tanda tangan teks.

## Jalankan

\`\`\`bash
pip install -e '.[migrasi,test]'
export RPI_DATABASE_URL='sqlite+pysqlite:////tmp/rpi-kbji.sqlite3'
# HANYA pada database baru. Untuk database lama harus gunakan prosedur migrasi aman.
alembic upgrade head

# Pemeriksaan read-only, belum menulis DB
python scripts/impor_kbji_ditinjau.py \
  --csv /path/kbji-kandidat.csv \
  --manifest /path/kbji-manifest.json \
  --berkas-asli /path/dokumen-sumber \
  --persetujuan /path/persetujuan-manusia.json

# Terapkan secara transaksional; semua baris selalu berstatus 'ditinjau'.
python scripts/impor_kbji_ditinjau.py \
  --csv /path/kbji-kandidat.csv \
  --manifest /path/kbji-manifest.json \
  --berkas-asli /path/dokumen-sumber \
  --persetujuan /path/persetujuan-manusia.json --terapkan
\`\`\`

Impor ulang paket identik bersifat idempoten. Kode dengan isi yang berbeda
ditolak dan transaksi dibatalkan; revisi memerlukan proses terpisah.

**Tidak pernah melakukan** promosi otomatis menjadi \`terverifikasi\`, penulisan
ke \`data/kbji_mappings.csv\`, atau perubahan pada tag v0.4.0.

## Yang masih harus dikerjakan

- Mengidentifikasi dokumen KBJI resmi beserta edisi dan aturan lisensi.
- Mendapat persetujuan reviewer independen dan riwayat keputusan yang dapat diaudit.
- Mengimpor taksonomi kandidat dan meninjau pemetaan 811 pekerjaan draf.
- Merancang tahapan publikasi data resmi hanya setelah bukti penerbit diverifikasi.

Tabel \`taksonomi_kbji_per_edisi\` diperkenalkan melalui migrasi
\`20261015_0600\`. Migrasi v0.4 tetap dipertahankan; rollback destruktif
tidak otomatis disediakan.
