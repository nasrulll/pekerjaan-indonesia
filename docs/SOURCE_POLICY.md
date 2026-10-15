# Kebijakan Sumber dan Verifikasi

**Jangan menyajikan entri kurasi awal sebagai data resmi BPS.**

1. **Sumber utama yang harus diperiksa:** publikasi Klasifikasi Baku Jabatan Indonesia (KBJI) dari BPS, beserta edisi/koreksi yang berlaku pada saat import. Pencarian unduhan resmi dan status edisi terbaru **belum diverifikasi dalam starter ini**.
2. **Sumber pelengkap:** nomenklatur jabatan ASN dari instansi yang berwenang (misalnya Kementerian PANRB/BKN), regulasi profesi berizin, dan publikasi lembaga profesi. Perbedaan nomenklatur dikelola sebagai entitas tersendiri.
3. **KBLI bukan KBJI.** Kode sektor editorial 39 bidang tidak boleh diperlakukan sebagai kode industri pemerintah.
4. Masukkan metadata di `sources.csv`: penerbit, judul, edisi, URI resmi, klasifikasi `official`, dan catatan lisensi. Jangan menggunakan domain atau judul palsu sebagai sumber.
5. Saat pemetaan, salin hanya elemen yang diizinkan untuk dipakai ulang. Periksa hak cipta, atribusi, lisensi, persyaratan distribusi, dan kebijakan privasi.
6. Tinjau hasil mapping dua tahap (pemeriksa dan reviewer), simpan alasan perbedaan, dan hindari verifikasi otomatis hanya berdasarkan kemiripan nama.
7. Ketika sumber resmi tidak tersedia, biarkan `kbji_mappings.csv` kosong; gunakan `record_status=draft`.
8. Cabang/pull request yang mengubah mapping harus menyertakan bukti sumber, edisi, metode penyelarasan dan dampak migrasi.

## Alur verifikasi resmi

1. Peroleh publikasi/salinan KBJI berlisensi yang sah.
2. Tentukan edisi dan granularity kode yang digunakan.
3. Catat sumber dalam `data/sources.csv`.
4. Buat mapping terhadap `occupation_id` dari `templates/kbji_mapping_template.csv`.
5. Jalankan `python scripts/validate.py` dan pemeriksaan manusia.
6. Ajukan PR, review, dan merge. Pertahankan mapping edisi sebelumnya.

**Batasan:** Validasi teknis memeriksa format/provenance dasar, **tidak** memeriksa kesesuaian substantif kode KBJI terhadap sumber asli. Review manual tetap wajib.


## Tambahan kebijakan pengupahan v0.3

- UMP dan UMK harus didukung keputusan resmi pemerintah daerah yang relevan untuk tahun berlaku; tidak boleh dicampur dengan rata-rata/median survei.
- Wilayah harus mempunyai `sistem_kode` dan catatan sumber. Kode dari BPS dan Kemendagri tidak boleh diperlakukan identik tanpa pemetaan verifikasi.
- Simpan ketidaktersediaan data sebagai tidak tersedia, bukan angka nol atau estimasi tersembunyi.
- Catat `satuan`, `cakupan_pekerja`, `jenis_data`, `tahun`, dan `jumlah_sampel` jika tersedia untuk statistik upah.
- Penyelarasan data upah menurut pekerjaan per kabupaten/kota hanya boleh dilakukan jika granularitas publikasi dan mutu sampelnya memadai.
