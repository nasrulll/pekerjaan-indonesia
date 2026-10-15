# Panduan Kontribusi

1. Buat branch `feat/nama-perubahan`, hindari commit langsung ke `main`.
2. Tambahkan pekerjaan baru sebagai baris CSV dengan `occupation_id` baru yang **tidak pernah digunakan**; setelah menghapus data, jangan gunakan ID lama.
3. Jika jabatan/gelar hanya variasi profesi yang sudah ada, tambahkan ke alias atau `job_titles.csv`, bukan menduplikasi pekerjaan tanpa alasan.
4. Kode KBJI resmi hanya dapat masuk jika ada metadata edisi, kode, label, sumber terdaftar, peninjau dan tanggal. Pembaruan mapping wajib diulas manusia.
5. Jangan mengubah `occupation_id` saat merapikan nama. Bila perlu pemisahan/penggabungan entri, jelaskan ID yang diganti dalam PR dan sediakan migrasi.
6. Jalankan:

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/build_sqlite.py
```

7. Sertakan konteks sumber, perubahan jumlah entri, serta risiko kompatibilitas API di deskripsi PR.
8. Kode dan dataset editorial awal dibuat untuk repositori contoh; pastikan lisensi dan atribusi data dari pihak ketiga sebelum kontribusi.

## Aturan tambahan RPI v0.4

- Ajukan kontribusi melalui PR dan gunakan template review; untuk sumber resmi cantumkan URL primer, edisi, tahun, lisensi, bukti verifikasi dan pemeriksa kedua.
- Jangan mengubah atau mendaur ulang `occupation_id`/`id_jabatan` yang sudah disetujui. Untuk penggantian nama, gunakan nama alternatif dan catat pemetaan lintas edisi.
- Tidak boleh menambahkan UMP/UMK atau nilai statistik rekaan, maupun mendistribusikan salinan berhak cipta tanpa izin.
- Untuk perubahan database, pastikan DDL bisa dikompilasi lintas dialek, siapkan jalur migrasi database yang sudah ada, serta tes rollback dan backup bila akan deploy.
