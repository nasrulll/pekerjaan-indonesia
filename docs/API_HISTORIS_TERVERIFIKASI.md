# API historis terverifikasi (pengembangan v0.5, issue #1–#3)

Endpoint berikut **baru**, terpisah dari API v0.4 lama:

- \`GET /v1/kbji/terverifikasi?edisi=...\`
- \`GET /v1/wilayah-historis/terverifikasi?sistem_kode=...&edisi=...\`
- \`GET /v1/upah-minimum-historis/terverifikasi?tahun=...&jenis_upah=UMP\`

Semua menerima \`batas\` (1–100) dan \`mulai\` (0–1.000.000),
mengembalikan \`pagination\`, \`data_tersedia\`, \`status_layanan\`, dan
\`catatan\`. Input menggunakan query terparameterisasi SQLAlchemy.

## Default: tertutup

Tanpa konfigurasi publikasi, seluruh endpoint mengembalikan daftar kosong.
Status \`ditinjau\` maupun \`draf\` **tidak ditampilkan**, bahkan ketika
sumber diizinkan secara eksplisit. Tidak ada endpoint tulis.

Untuk menyiapkan publikasi **hanya setelah izin dan persetujuan manusia
yang sebenarnya diperiksa di luar sistem**, pengelola dapat menyetel:

\`\`\`bash
RPI_PUBLIKASI_HISTORIS=aktif
RPI_SUMBER_DISETUJUI_PUBLIK='ID-SUMBER-RESMI-1,ID-SUMBER-RESMI-2'
\`\`\`

**Jangan menyetel variabel tersebut berdasarkan data kandidat atau tanpa review
sumber primer.** Semua ID yang berawalan \`KANDIDAT-\` atau \`KAND-\` dikecualikan
oleh kode, sehingga importer kandidat tidak dapat memublikasikan data hanya
dengan mengganti status menjadi \`terverifikasi\`.

Meski fitur aktif, respons hanya berisi entri berstatus \`terverifikasi\`
yang ditautkan ke sumber dengan status, jenis, edisi, bukti izin, checksum
dan peninjau yang tercatat. Untuk KBJI/wilayah, induk wajib terverifikasi.
Untuk UMP/UMK, referensi wilayah dan induknya juga wajib terverifikasi.
Hanya keputusan upah berstatus \`berlaku\` untuk **tahun masing-masing** yang
ditampilkan; keputusan yang sudah diganti/discabut tidak disajikan sebagai
nilai yang berlaku. Jika terdapat keputusan aktif ganda, nilai pada kelompok
tersebut disembunyikan.

## Batasan penting

1. Operator harus memverifikasi autentisitas sumber, legalitas izin, dan
   isi nominal/kode terhadap dokumen primer. Metadata yang valid secara
   sintaksis bukan bukti keaslian pemerintah.
2. Daftar ID yang diperbolehkan merupakan **mekanisme konfigurasi rilis**,
   bukan tanda tangan kriptografis atau prosedur persetujuan multipihak.
3. Jika migrasi historis belum tersedia tetapi konfigurasi publikasi telah
   diaktifkan, API mengembalikan 503, bukan angka kosong yang menyesatkan.
4. Kode lama \`/v1/wilayah\`, \`/v1/upah-minimum\` dan \`/v1/kbji/codes\`
   tetap tersedia dan tidak dialihkan secara diam-diam.
5. Data resmi dari BPS dan keputusan pemerintah masih belum tersedia di repo.
   Dalam konfigurasi standar, endpoint akan selalu kosong.
6. RPI v0.4.0 tetap baseline terkunci; pengembangan ini belum menjadi rilis stabil.
