-- Ekstensi Bahasa Indonesia v0.3.0. Kode wilayah adalah TEXT agar angka nol awal tidak hilang.
CREATE TABLE jabatan_nasional (
 id_jabatan TEXT PRIMARY KEY,
 nama_jabatan TEXT NOT NULL,
 id_pekerjaan TEXT NOT NULL REFERENCES occupations(occupation_id),
 jenis_jabatan TEXT NOT NULL,
 id_jabatan_induk TEXT REFERENCES jabatan_nasional(id_jabatan),
 jenjang TEXT, kode_konteks TEXT REFERENCES employment_contexts(context_code),
 sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi TEXT NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi TEXT, catatan TEXT,
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE wilayah_administratif (
 sistem_kode TEXT NOT NULL, kode_wilayah TEXT NOT NULL,
 nama_wilayah TEXT NOT NULL,
 jenis_wilayah TEXT NOT NULL CHECK(jenis_wilayah IN ('provinsi','kabupaten','kota')),
 kode_induk TEXT,
 sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi TEXT NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi TEXT,
 PRIMARY KEY(sistem_kode,kode_wilayah),
 FOREIGN KEY(sistem_kode,kode_induk) REFERENCES wilayah_administratif(sistem_kode,kode_wilayah),
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE pemetaan_jabatan_kbji (
 id_jabatan TEXT NOT NULL REFERENCES jabatan_nasional(id_jabatan),
 edisi_kbji TEXT NOT NULL, kode_kbji TEXT NOT NULL, nama_kbji TEXT NOT NULL,
 sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 diverifikasi_oleh TEXT NOT NULL, tanggal_verifikasi TEXT NOT NULL,
 PRIMARY KEY(id_jabatan,edisi_kbji,kode_kbji)
);
CREATE TABLE kompetensi_jabatan (
 id_kompetensi TEXT PRIMARY KEY,
 id_jabatan TEXT NOT NULL REFERENCES jabatan_nasional(id_jabatan),
 nama_kompetensi TEXT NOT NULL,
 kategori TEXT NOT NULL, tingkat TEXT,
 sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi TEXT NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi'))
);
CREATE TABLE upah_minimum (
 id_upah TEXT PRIMARY KEY,
 sistem_kode TEXT NOT NULL, kode_wilayah TEXT NOT NULL,
 tahun INTEGER NOT NULL CHECK(tahun BETWEEN 1900 AND 2200),
 jenis_upah TEXT NOT NULL CHECK(jenis_upah IN ('UMP','UMK')),
 nilai_rupiah INTEGER NOT NULL CHECK(nilai_rupiah > 0),
 tanggal_mulai TEXT NOT NULL,
 sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi TEXT NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi TEXT, catatan TEXT,
 FOREIGN KEY(sistem_kode,kode_wilayah) REFERENCES wilayah_administratif(sistem_kode,kode_wilayah),
 UNIQUE(sistem_kode,kode_wilayah,tahun,jenis_upah),
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE statistik_upah (
 id_statistik TEXT PRIMARY KEY,
 sistem_kode TEXT NOT NULL, kode_wilayah TEXT NOT NULL,
 tahun INTEGER NOT NULL CHECK(tahun BETWEEN 1900 AND 2200),
 id_pekerjaan TEXT REFERENCES occupations(occupation_id),
 id_jabatan TEXT REFERENCES jabatan_nasional(id_jabatan),
 metrik TEXT NOT NULL CHECK(metrik IN ('rata_rata','median','persentil_25','persentil_75')),
 nilai_rupiah INTEGER NOT NULL CHECK(nilai_rupiah >= 0),
 satuan TEXT NOT NULL CHECK(satuan IN ('per_bulan','per_jam')),
 cakupan_pekerja TEXT NOT NULL CHECK(cakupan_pekerja IN ('semua','formal','informal')),
 jenis_data TEXT NOT NULL CHECK(jenis_data IN ('resmi','survei','estimasi')),
 jumlah_sampel INTEGER CHECK(jumlah_sampel IS NULL OR jumlah_sampel >= 0),
 sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi TEXT NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi TEXT, catatan TEXT,
 FOREIGN KEY(sistem_kode,kode_wilayah) REFERENCES wilayah_administratif(sistem_kode,kode_wilayah),
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE kelas_gaji (
 id_kelas_gaji TEXT PRIMARY KEY,
 sistem_penggajian TEXT NOT NULL, kode_kelas TEXT NOT NULL,
 nama_kelas TEXT NOT NULL,
 nilai_dasar_rupiah INTEGER CHECK(nilai_dasar_rupiah IS NULL OR nilai_dasar_rupiah >= 0),
 tahun INTEGER NOT NULL CHECK(tahun BETWEEN 1900 AND 2200),
 sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi TEXT NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 UNIQUE(sistem_penggajian,kode_kelas,tahun)
);
CREATE TABLE riwayat_impor (
 id_impor TEXT PRIMARY KEY,
 nama_dataset TEXT NOT NULL, versi_dataset TEXT,
 jumlah_rekaman INTEGER NOT NULL CHECK(jumlah_rekaman >= 0),
 hash_sha256 TEXT NOT NULL, sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 waktu_impor TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('berhasil','gagal','ditolak'))
);
CREATE INDEX idx_jabatan_pekerjaan ON jabatan_nasional(id_pekerjaan);
CREATE INDEX idx_wilayah_induk ON wilayah_administratif(sistem_kode,kode_induk);
CREATE INDEX idx_upah_minimum_wilayah ON upah_minimum(sistem_kode,kode_wilayah,tahun);
CREATE INDEX idx_statistik_upah_wilayah ON statistik_upah(sistem_kode,kode_wilayah,tahun,metrik);

-- Penambahan lintas klasifikasi internasional dan versi rilis (v0.4).
CREATE TABLE pemetaan_internasional (
 id_pemetaan TEXT PRIMARY KEY, id_pekerjaan TEXT NOT NULL REFERENCES occupations(occupation_id),
 sistem_klasifikasi TEXT NOT NULL, edisi TEXT NOT NULL, kode TEXT NOT NULL,
 nama_resmi TEXT NOT NULL, sumber_id TEXT NOT NULL REFERENCES data_sources(source_id),
 diverifikasi_oleh TEXT NOT NULL, tanggal_verifikasi TEXT NOT NULL,
 UNIQUE(id_pekerjaan,sistem_klasifikasi,edisi,kode));
CREATE TABLE riwayat_rilis (versi TEXT PRIMARY KEY, hash_manifest TEXT NOT NULL,
 waktu_rilis TEXT NOT NULL, status TEXT NOT NULL);
