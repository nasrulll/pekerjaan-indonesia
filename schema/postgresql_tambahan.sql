-- Migrasi penambahan v0.3.0; aman dijalankan ulang dan tidak menghapus tabel versi lama.
CREATE TABLE IF NOT EXISTS jabatan_nasional (
 id_jabatan text PRIMARY KEY,
 nama_jabatan text NOT NULL,
 id_pekerjaan text NOT NULL REFERENCES occupations(occupation_id),
 jenis_jabatan text NOT NULL,
 id_jabatan_induk text REFERENCES jabatan_nasional(id_jabatan),
 jenjang text, kode_konteks text REFERENCES employment_contexts(context_code),
 sumber_id text NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi text NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi date, catatan text,
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS wilayah_administratif (
 sistem_kode text NOT NULL, kode_wilayah text NOT NULL,
 nama_wilayah text NOT NULL,
 jenis_wilayah text NOT NULL CHECK(jenis_wilayah IN ('provinsi','kabupaten','kota')),
 kode_induk text,
 sumber_id text NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi text NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi date,
 PRIMARY KEY(sistem_kode,kode_wilayah),
 FOREIGN KEY(sistem_kode,kode_induk) REFERENCES wilayah_administratif(sistem_kode,kode_wilayah),
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS pemetaan_jabatan_kbji (
 id_jabatan text NOT NULL REFERENCES jabatan_nasional(id_jabatan),
 edisi_kbji text NOT NULL, kode_kbji text NOT NULL, nama_kbji text NOT NULL,
 sumber_id text NOT NULL REFERENCES data_sources(source_id),
 diverifikasi_oleh text NOT NULL, tanggal_verifikasi date NOT NULL,
 PRIMARY KEY(id_jabatan,edisi_kbji,kode_kbji)
);
CREATE TABLE IF NOT EXISTS kompetensi_jabatan (
 id_kompetensi text PRIMARY KEY,
 id_jabatan text NOT NULL REFERENCES jabatan_nasional(id_jabatan),
 nama_kompetensi text NOT NULL,
 kategori text NOT NULL, tingkat text,
 sumber_id text NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi text NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi'))
);
CREATE TABLE IF NOT EXISTS upah_minimum (
 id_upah text PRIMARY KEY,
 sistem_kode text NOT NULL, kode_wilayah text NOT NULL,
 tahun integer NOT NULL CHECK(tahun BETWEEN 1900 AND 2200),
 jenis_upah text NOT NULL CHECK(jenis_upah IN ('UMP','UMK')),
 nilai_rupiah bigint NOT NULL CHECK(nilai_rupiah > 0),
 tanggal_mulai date NOT NULL,
 sumber_id text NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi text NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi date, catatan text,
 FOREIGN KEY(sistem_kode,kode_wilayah) REFERENCES wilayah_administratif(sistem_kode,kode_wilayah),
 UNIQUE(sistem_kode,kode_wilayah,tahun,jenis_upah),
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS statistik_upah (
 id_statistik text PRIMARY KEY,
 sistem_kode text NOT NULL, kode_wilayah text NOT NULL,
 tahun integer NOT NULL CHECK(tahun BETWEEN 1900 AND 2200),
 id_pekerjaan text REFERENCES occupations(occupation_id),
 id_jabatan text REFERENCES jabatan_nasional(id_jabatan),
 metrik text NOT NULL CHECK(metrik IN ('rata_rata','median','persentil_25','persentil_75')),
 nilai_rupiah bigint NOT NULL CHECK(nilai_rupiah >= 0),
 satuan text NOT NULL CHECK(satuan IN ('per_bulan','per_jam')),
 cakupan_pekerja text NOT NULL CHECK(cakupan_pekerja IN ('semua','formal','informal')),
 jenis_data text NOT NULL CHECK(jenis_data IN ('resmi','survei','estimasi')),
 jumlah_sampel integer CHECK(jumlah_sampel IS NULL OR jumlah_sampel >= 0),
 sumber_id text NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi text NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 tanggal_verifikasi date, catatan text,
 FOREIGN KEY(sistem_kode,kode_wilayah) REFERENCES wilayah_administratif(sistem_kode,kode_wilayah),
 CHECK(status_verifikasi='draf' OR tanggal_verifikasi IS NOT NULL)
);
CREATE TABLE IF NOT EXISTS kelas_gaji (
 id_kelas_gaji text PRIMARY KEY,
 sistem_penggajian text NOT NULL, kode_kelas text NOT NULL,
 nama_kelas text NOT NULL,
 nilai_dasar_rupiah bigint CHECK(nilai_dasar_rupiah IS NULL OR nilai_dasar_rupiah >= 0),
 tahun integer NOT NULL CHECK(tahun BETWEEN 1900 AND 2200),
 sumber_id text NOT NULL REFERENCES data_sources(source_id),
 status_verifikasi text NOT NULL CHECK(status_verifikasi IN ('draf','terverifikasi')),
 UNIQUE(sistem_penggajian,kode_kelas,tahun)
);
CREATE TABLE IF NOT EXISTS riwayat_impor (
 id_impor text PRIMARY KEY,
 nama_dataset text NOT NULL, versi_dataset text,
 jumlah_rekaman integer NOT NULL CHECK(jumlah_rekaman >= 0),
 hash_sha256 text NOT NULL, sumber_id text NOT NULL REFERENCES data_sources(source_id),
 waktu_impor timestamptz NOT NULL,
 status text NOT NULL CHECK(status IN ('berhasil','gagal','ditolak'))
);
CREATE INDEX IF NOT EXISTS idx_jabatan_pekerjaan ON jabatan_nasional(id_pekerjaan);
CREATE INDEX IF NOT EXISTS idx_wilayah_induk ON wilayah_administratif(sistem_kode,kode_induk);
CREATE INDEX IF NOT EXISTS idx_upah_minimum_wilayah ON upah_minimum(sistem_kode,kode_wilayah,tahun);
CREATE INDEX IF NOT EXISTS idx_statistik_upah_wilayah ON statistik_upah(sistem_kode,kode_wilayah,tahun,metrik);
