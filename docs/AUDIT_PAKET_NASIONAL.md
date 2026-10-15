# Gerbang audit paket nasional — RPI v0.5 (issue #1, #2, #3)

Alat ini menggabungkan audit KBJI, wilayah, dan keputusan UMP/UMK dalam satu pemeriksaan.
**Tidak mengunduh sumber, mengubah data induk, atau menerbitkan data resmi.**

## Contoh penggunaan

```bash
python scripts/audit_paket_nasional.py \
  --kbji /path/kbji.csv --manifest-kbji /path/kbji.json \
  --wilayah /path/wilayah.csv --manifest-wilayah /path/wilayah.json \
  --upah /path/upah.csv --manifest-upah /path/upah.json \
  --pekerjaan data/occupations.csv \
  --berkas-asli-kbji /path/sumber-kbji \
  --berkas-asli-wilayah /path/sumber-wilayah \
  --berkas-asli-upah /path/dokumen-keputusan \
  --laporan /tmp/laporan-paket.json
```

Boleh memeriksa KBJI atau wilayah secara mandiri. Audit upah wajib menyertakan wilayah.
Manifest upah wajib mencantumkan `edisi_wilayah` yang cocok dengan CSV wilayah.
Berikan berkas asli untuk menguji checksum SHA-256; tanpa berkas tersebut laporan memberi peringatan.
SHA-256 tidak membuktikan keaslian penerbit atau hak redistribusi.

## Pemeriksaan tambahan

- Edisi CSV KBJI dan wilayah harus sama dengan manifest.
- Keputusan upah harus mengacu wilayah dalam sistem kode/edisi yang sama.
- Penggantian keputusan harus terhubung dalam wilayah, tahun, edisi, dan jenis upah yang sama.
- Tidak boleh ada rantai keputusan siklik, pengganti ganda, maupun keputusan 'diganti' tanpa penerus.
- Kecocokan judul pekerjaan dengan kode KBJI tetap kandidat, bukan verifikasi.

Nilai `layak_diajukan_untuk_tinjauan=true` berarti tidak ada galat otomatis.
Status publikasi **selalu diblokir** sampai ada persetujuan manusia dan sumber primer berizin.

Belum dikerjakan: akuisisi dan izin sumber resmi, impor KBJI dan seluruh wilayah,
pemeriksaan keputusan pemerintah, pemetaan 811 draf pekerjaan, serta publikasi data resmi.
Lanjutkan sesuai issue #1, #2, dan #3 melalui PR khusus untuk dataset yang sudah disetujui.
