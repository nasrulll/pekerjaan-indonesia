# Audit katalog KBJI — proses RPI v0.5.0

> **Status:** alat audit draf sudah tersedia, tetapi **belum ada data KBJI resmi yang diimpor**. Contoh kode buatan tidak boleh dipublikasikan sebagai kode KBJI.

## Langkah

1. Tentukan edisi klasifikasi dan salinan publikasi dari instansi penerbit; verifikasi informasi dan hak penggunaan ulang secara manual.
2. Salin `templates/kbji_manifest_template.json` sebagai manifest kerja. Isi penerbit, judul, edisi, URL HTTPS, tanggal, izin distribusi, dan hash SHA-256 sumber primer yang telah diperiksa. Jangan pernah menaruh salinan dokumen berlisensi terbatas dalam repository.
3. Konversikan taksonomi menjadi CSV UTF-8 dengan header `edisi,kode,nama,kode_induk,tingkat`. **Kode harus string** supaya nol awal tidak hilang; kode induk kosong hanya untuk akar. Tingkat dihitung dari 1; hubungan induk harus eksplisit.
4. Jalankan pemeriksaan taksonomi sebelum ada perubahan basis data.

```bash
python scripts/validasi_manifest_sumber.py /path/manifest.json

python scripts/audit_kbji.py \
  --csv-kbji /path/kbji-kandidat.csv \
  --manifest /path/manifest.json \
  --csv-pekerjaan data/occupations.csv \
  --laporan /tmp/audit-kbji.json \
  --kandidat /tmp/kandidat-kbji.csv
```

5. Tinjau kesalahan edisi, kode ganda, hubungan induk, siklus, tingkat, dan identitas sumber. Kandidat kecocokan nama hanya berupa **usulan untuk peninjau manusia**, sekalipun teksnya persis sama.
6. Setelah peninjau memeriksa keaslian, ketepatan taksonomi, hak redistribusi, dan pemetaan, lakukan pengembangan skema serta impor versi resmi lewat PR tersendiri. Jangan menaruh hasil audit pada `data/kbji_mappings.csv` secara otomatis.

## Pembatasan keamanan

- Alat `audit_kbji.py` tidak menulis ke DB atau mengubah CSV induk; keluaran hanya laporan dan kandidat.
- Manifest dengan `status=terverifikasi` **ditolak oleh alat audit** karena alat ini bukan mekanisme persetujuan sumber.
- Checksum pada laporan adalah hash CSV hasil olahan; **bukan** verifikasi atas berkas primer yang disebut manifest.
- URL HTTPS yang valid secara sintaksis bukan bukti domain instansi penerbit.
- Klasifikasi antar-edisi tidak boleh digabung atau ditimpa.
- RPI masih menyediakan **811 entri draf**, bukan 811 kode KBJI resmi.

Lihat [issue #1](https://github.com/nasrulll/pekerjaan-indonesia/issues/1) dan [rencana impor](RENCANA_IMPOR_KBJI_V05.md) untuk kriteria penerimaan.
