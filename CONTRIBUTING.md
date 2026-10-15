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
