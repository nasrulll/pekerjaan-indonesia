# Penyegaran dan kendali mutu data resmi

Tidak ada API resmi nasional yang boleh dianggap tersedia tanpa verifikasi. RPI **tidak** melakukan scraping tanpa otorisasi atau menerbitkan sumber sebagai terverifikasi otomatis.

1. Unduh sumber dari penerbit berwenang, periksa lisensi penggunaan ulang dan keaslian dokumen.
2. Rekam `source_id`, judul, penerbit, edisi, URI, tahun, hak distribusi, dan penanggung jawab review di `data/sources.csv`.
3. Siapkan paket CSV yang hanya berisi file dari allowlist `scripts/sinkronisasi_data.py`, plus `manifest-sumber.json` yang memuat `{ "versi":"2026-...", "asal_sumber":"penerbit + edisi", "berkas":{"upah_minimum.csv":"<64 digit hash SHA-256>"} }`. Paket harus berisi file CSV penuh per tabel, bukan delta parsial.
4. Jalankan `python scripts/sinkronisasi_data.py ./paket` untuk simulasi dan validasi semua referensi silang. Jangan menandai draf sebagai terverifikasi tanpa bukti dan peninjauan manusia.
5. Buka Pull Request, bandingkan perubahan, pastikan kode yang sudah dipublikasi dan ID stabil. Reviu dua pihak untuk sumber regulatif.
6. Setelah disetujui, jalankan `--terapkan`, validasi lagi, commit, buat release dengan checksum, kemudian impor ke tiap database terdaftar; pertahankan backup Git tag sebagai rollback.
7. Jika proses terputus saat beberapa berkas diganti, pulihkan dari Git. Penggantian setiap file bersifat atomik, **batch antarfile belum** transaksional penuh. Jalankan dalam clone kerja terpisah.

**Jadwal yang disarankan:** pemeriksaan sumber upah setiap tahun setelah keputusan resmi terbit; perubahan klasifikasi/ASN dan wilayah ketika publikasi diterbitkan. GitHub workflow bisa mengingatkan maintainer, tetapi tidak mengumpulkan data pemerintah otomatis tanpa konektor yang disetujui.
