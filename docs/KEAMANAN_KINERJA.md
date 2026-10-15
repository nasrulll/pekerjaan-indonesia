# Keamanan, kinerja dan kriteria rilis stabil

**Keamanan:** API baca-saja, parameter SQL dibind, whitelist database URL dan input, CORS hanya untuk origin yang dipercaya; rahasia layanan melalui env/secrets. TLS dan rate limiting di reverse proxy wajib untuk layanan publik. Audit akses, otorisasi operator impor, backup terenkripsi, dan pemulihan bencana belum diuji produksi.

**Kualitas data:** identitas stabil, edisi KBJI, sumber dan reviewer; wilayah berkode string bersumber; UMP/UMK tidak digabung dengan rata-rata/median; data estimasi berlabel, tanpa angka palsu; missing bukan 0.

**Kinerja:** indeks pekerjaan/jabatan/wilayah/upah dalam skema; pembatasan halaman API 100. Pencarian cerdas masih berbasis nama/sinonim dan peringkat deterministik, bukan layanan NLP atau vector search. Cari pekerjaan melakukan sorting hasil di memori: audit performa kembali pada dataset jauh lebih besar. Analitik tidak menghasilkan rata-rata dari rata-rata observasi yang berbeda. Uji beban concurrency, multi-tenant, tuning indeks riil dan partisi masa depan belum dilakukan.

**Gerbang rilis v1.0:** seluruh klasifikasi/lisensi yang menjadi klaim resmi diverifikasi dari rujukan primer; setidaknya satu pengujian integrasi nyata untuk tiap adapter yang dinyatakan didukung produksi; migrasi dan rollback teruji; CI lintas versi; audit keamanan pihak independen; evaluasi privasi statistik granular; dokumentasi dan pengguna uji mencoba end-to-end. Sampai itu terpenuhi gunakan label **prarilis**.
