# Persiapan referensi wilayah RPI v0.5.0

**Status:** belum ada kode wilayah resmi BPS atau Kemendagri yang diimpor. Alat audit ini hanya menerima **kandidat dataset untuk peninjauan**, bukan sumber resmi.

## Pemisahan sistem kode dan edisi

Satu kode wilayah dapat berbeda arti menurut instansi, sistem pengkodean, dan waktu. Karenanya, berkas audit menggunakan identitas gabungan `(sistem_kode, edisi, kode_wilayah)`, bukan hanya kode wilayah. Nilai tetap string agar nol awal dan pemisah kode tidak hilang.

Format CSV: [template](../templates/wilayah_taksonomi_template.csv).

```bash
python scripts/audit_wilayah.py \
  --csv /path/kode-wilayah-kandidat.csv \
  --laporan /tmp/audit-wilayah.json
```

Validasi meliputi keunikan sistem/edisi/kode, keharusan induk pada kabupaten/kota, larangan induk pada provinsi, dan kecocokan induk dengan provinsi dalam **sistem serta edisi yang sama**.

## Gerbang sebelum impor resmi

1. Verifikasi instansi penerbit, versi/edisi, tanggal berlaku, URL primer, checksum berkas asli dan izin redistribusi.
2. Bandingkan daftar dan hierarki seluruh wilayah dengan publikasi resmi, termasuk pemekaran, penggabungan serta perubahan nama dan kode.
3. Buat catatan perubahan antar-edisi. Jangan otomatis menimpa data historis pada `data/wilayah_administratif.csv`.
4. Rancang serta uji migrasi skema berversi untuk menyimpan edisi historis, karena tabel operasional v0.4.0 menggunakan pasangan `(sistem_kode, kode_wilayah)` saja.
5. Jalankan pengujian dan tinjauan manusia sebelum mengimpor atau mengekspos sebagai `terverifikasi`.

**Penting:** hasil audit bukan sertifikasi data pemerintah. Lanjutkan [issue #2](https://github.com/nasrulll/pekerjaan-indonesia/issues/2) setelah sumber resmi berizin tersedia.
