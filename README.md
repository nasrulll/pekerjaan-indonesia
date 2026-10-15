# Pekerjaan Indonesia / NOR-ID

**Repositori Git untuk katalog nasional pekerjaan, profesi, spesialisasi, dan jabatan di Indonesia.**

> **Status: starter v0.1.0, bukan referensi resmi pemerintah.** Repositori ini saat pertama dibuat memiliki **811 judul pekerjaan awal dalam 39 sektor editorial**. Seluruh entri pekerjaan masih `draft`; **belum ada kode KBJI individu yang diklaim sudah diverifikasi**. Jumlah pekerjaan di Indonesia tidak dibatasi pada 811: cakupan lengkap baru dapat diklaim setelah rekonsiliasi dengan sumber resmi KBJI dan pemeriksaan profesi/spesialisasi lokal.

## Prinsip dasar

1. **Pekerjaan ≠ jabatan organisasi ≠ status kepegawaian ≠ bidang usaha.** Contoh: "perawat" adalah pekerjaan; "kepala ruang" adalah jabatan; "PNS/PPPK/swasta" adalah konteks kepegawaian; KBLI mengklasifikasikan kegiatan usaha.
2. **KBJI** adalah acuan klasifikasi pekerjaan. **KBLI** digunakan hanya jika diperlukan untuk hubungan bidang usaha. Jangan mengarang kode KBJI atau menganggap 39 sektor editorial sama dengan taksonomi resmi.
3. Kode resmi ditambahkan melalui `data/kbji_mappings.csv` dengan *edisi, kode, label sumber, ID sumber, pemeriksa, dan tanggal verifikasi*.
4. **ID internal stabil** (`ID-OCC-000001` dst.), tidak berubah ketika nama/label disesuaikan. Jangan gunakan nomor baris sebagai ID.
5. Semua perubahan bisa diaudit lewat Git: *pull request*, *review*, dan *CI*.
6. Sumber resmi eksternal tetap tunduk pada syarat lisensi masing-masing; jangan menyalin keseluruhan publikasi tanpa memastikan hak penggunaannya.

## Struktur

```text
pekerjaan-indonesia/
├── .github/workflows/ci.yml          # validasi otomatis di setiap PR
├── data/
│   ├── occupations.csv              # 811 judul pekerjaan, draft kurasi
│   ├── kbji_mappings.csv            # kosong sampai verifikasi resmi
│   ├── job_titles.csv               # contoh jabatan & jenjang
│   ├── sources.csv                  # provenance sumber
│   └── reference/
│       ├── sectors.csv              # 39 sektor editorial
│       ├── kbji_major_groups.csv    # 10 kelompok utama
│       └── employment_contexts.csv  # PNS, PPPK, BUMN, swasta, dll.
├── docs/
│   ├── DATA_DICTIONARY.md
│   ├── SOURCE_POLICY.md
│   ├── ROADMAP.md
│   └── INTEGRATION_SKPGEN.md
├── schema/
│   ├── postgresql.sql               # model database produksi
│   └── occupation.schema.json
├── scripts/
│   ├── validate.py
│   ├── build_sqlite.py
│   ├── search.py
│   └── export_json.py
├── templates/kbji_mapping_template.csv
└── tests/test_catalog.py
```

## Cara cepat menjalankan (Python 3.10+ tanpa dependensi eksternal)

```bash
python scripts/validate.py
python -m unittest discover -s tests -v
python scripts/build_sqlite.py
python scripts/search.py "guru"
python scripts/search.py "dokter" --sector kesehatan --limit 15
python scripts/export_json.py
```

Hasil build lokal (tidak masuk Git) ada di `dist/pekerjaan-indonesia.sqlite3` dan `dist/occupations.json`. `schema/postgresql.sql` adalah skema produksi awal dan **tidak otomatis diisi oleh pembangun SQLite**; ingestion PostgreSQL merupakan pekerjaan lanjutan.

## Membuat repositori GitHub

```bash
git init

git add .
git commit -m "feat: bootstrap katalog pekerjaan Indonesia v0.1.0"
# Buat repository kosong di GitHub terlebih dahulu, misalnya pekerjaan-indonesia
# Ganti OWNER dengan akun/organisasi GitHub Anda.
git branch -M main
git remote add origin https://github.com/OWNER/pekerjaan-indonesia.git
git push -u origin main
```

> Untuk arsip yang sudah memiliki riwayat Git, pengguna dapat menjalankan `git clone pekerjaan-indonesia.git.bundle pekerjaan-indonesia` dari berkas bundle yang disediakan. Nama `OWNER` hanya contoh dan belum menunjuk repositori aktif.

## Kriteria data terverifikasi

- Satu entri terhubung ke sumber asli dan edisi resmi yang teridentifikasi.
- Pemetaannya ditinjau oleh manusia; sekadar nama mirip belum berarti klasifikasi benar.
- Kode angka disimpan sebagai **teks** untuk mempertahankan angka nol di depan.
- Status `published` hanya setelah QA, pemeriksaan duplikat, istilah dan perubahan versi.
- Crosswalk dari satu edisi KBJI ke edisi lain disimpan sebagai mapping baru, bukan overwrite.

## Kontribusi

Lihat [CONTRIBUTING.md](CONTRIBUTING.md), [kamus data](docs/DATA_DICTIONARY.md), [kebijakan sumber](docs/SOURCE_POLICY.md), dan [roadmap](docs/ROADMAP.md).
