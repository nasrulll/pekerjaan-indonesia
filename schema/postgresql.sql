-- NOR-ID / Pekerjaan Indonesia - PostgreSQL schema v0.2
-- Official KBJI/KBLI codes are stored only when source verified.
BEGIN;
CREATE TABLE IF NOT EXISTS data_sources (
  source_id text PRIMARY KEY,
  title text NOT NULL,
  publisher text NOT NULL,
  edition text,
  uri text,
  kind text NOT NULL CHECK (kind IN ('official','internal','academic','other')),
  license_note text
);

CREATE TABLE IF NOT EXISTS sectors (
  sector_id text PRIMARY KEY,
  sector_name text NOT NULL UNIQUE,
  sector_type text NOT NULL DEFAULT 'editorial' CHECK(sector_type IN ('editorial','official_kbli')),
  official_kbli_code text -- nullable until source verified; KBLI is an activity classification
);

CREATE TABLE IF NOT EXISTS occupations (
  occupation_id text PRIMARY KEY CHECK (occupation_id ~ '^ID-OCC-[0-9]{6}$'),
  preferred_name_id text NOT NULL,
  alternative_names text NOT NULL DEFAULT '',
  sector_id text NOT NULL REFERENCES sectors(sector_id),
  description_id text,
  source_id text NOT NULL REFERENCES data_sources(source_id),
  record_status text NOT NULL DEFAULT 'draft' CHECK(record_status IN ('draft','reviewed','published','archived')),
  last_reviewed date,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(preferred_name_id,sector_id)
);

-- Allow upgrading a database initialized with the v0.1 schema.
ALTER TABLE occupations ADD COLUMN IF NOT EXISTS alternative_names text NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS occupation_aliases (
  alias_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  occupation_id text NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
  alternative_name_id text NOT NULL,
  UNIQUE (occupation_id,alternative_name_id)
);

CREATE TABLE IF NOT EXISTS kbji_mappings (
  occupation_id text NOT NULL REFERENCES occupations(occupation_id),
  kbji_edition text NOT NULL,
  kbji_code text NOT NULL CHECK (kbji_code ~ '^[0-9]{1,8}$'),
  kbji_label_id text NOT NULL,
  source_id text NOT NULL REFERENCES data_sources(source_id),
  verified_by text NOT NULL,
  verified_at date NOT NULL,
  PRIMARY KEY (occupation_id,kbji_edition,kbji_code)
);

CREATE TABLE IF NOT EXISTS employment_contexts (
  context_code text PRIMARY KEY,
  label_id text NOT NULL,
  dimension text NOT NULL CHECK(dimension IN ('employment_status','employer_sector','work_arrangement'))
);

-- A person may hold a title in multiple contexts. Context is not part of the occupational identity.
CREATE TABLE IF NOT EXISTS job_titles (
  title_id text PRIMARY KEY,
  title_name_id text NOT NULL,
  occupation_id text NOT NULL REFERENCES occupations(occupation_id),
  seniority_level text,
  context_code text REFERENCES employment_contexts(context_code),
  notes text
);

CREATE TABLE IF NOT EXISTS occupation_reviews (
  review_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  occupation_id text NOT NULL REFERENCES occupations(occupation_id),
  reviewer text NOT NULL,
  outcome text NOT NULL CHECK(outcome IN ('approved','rejected','needs_changes')),
  notes text,
  reviewed_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_occupation_name ON occupations(preferred_name_id);
CREATE INDEX IF NOT EXISTS ix_occupation_sector ON occupations(sector_id);
CREATE INDEX IF NOT EXISTS ix_occupation_status ON occupations(record_status);
CREATE INDEX IF NOT EXISTS ix_kbji_code ON kbji_mappings(kbji_edition,kbji_code);
CREATE INDEX IF NOT EXISTS ix_title_occupation ON job_titles(occupation_id);

-- Tabel v0.3 berbahasa Indonesia
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

COMMIT;
