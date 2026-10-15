# Audit keputusan upah minimum — RPI v0.5.0

**Status data:** repositori belum berisi angka UMP/UMK resmi terverifikasi. Berkas contoh dan pengujian hanya memakai data sintetis.

## Prinsip
- **UMP adalah upah minimum provinsi**, UMK adalah upah minimum kabupaten/kota yang ditetapkan. Keduanya **bukan** statistik rata-rata atau median gaji pekerja.
- Keputusan berisi nominal rupiah, tahun keberlakuan, tanggal berlaku, tanggal dan nomor keputusan, penerbit serta URL bukti. Catat penggantian/pencabutan secara terpisah.
- Periksa dokumen keputusan asli, instansi penerbit, perubahan keputusan, status hukumnya, batas cakupan, dan izin penggunaan ulang secara manual.
- Kode wilayah harus sesuai satu **sistem kode dan edisi**, tidak cukup mencocokkan nama kota.
- Tidak semua kabupaten/kota memiliki UMK sendiri; jangan mengarang nilai ketika tidak ditemukan.

## Audit kandidat sebelum impor

Buat CSV kandidat dari [template upah](../templates/upah_minimum_keputusan_template.csv) dan referensi kode wilayah dari [template wilayah](../templates/wilayah_taksonomi_template.csv), setelah memeriksa sumbernya.

```bash
python scripts/audit_upah_minimum.py \
  --csv-upah /path/upah-keputusan-kandidat.csv \
  --csv-wilayah /path/wilayah-kandidat.csv \
  --laporan /tmp/audit-upah-minimum.json
```

Pemeriksaan mencakup pembatasan UMP/UMK menurut tingkat wilayah, tahun, rupiah positif, tanggal kalender, URL HTTPS, dokumen keputusan ganda, dan maksimum satu keputusan berstatus `berlaku` pada wilayah/tahun/jenis yang sama.

**Batasan desain saat ini:** tabel `upah_minimum` v0.4.0 hanya mengizinkan satu nilai per wilayah/tahun/jenis. Sebelum memuat revisi keputusan, perlu migrasi tersendiri untuk histori keputusan, edisi wilayah, dan keterkaitan keputusan yang digantikan. Audit ini tidak mengubah tabel produksi, tidak memvalidasi identitas instansi secara daring, dan tidak menyatakan nominal apa pun sebagai data resmi.

Lanjutkan pengadaan sumber dan review sesuai [issue #3](https://github.com/nasrulll/pekerjaan-indonesia/issues/3).
