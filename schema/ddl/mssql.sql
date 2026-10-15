-- RPI 0.4 skema baru mssql. Pratinjau DBA; BUKAN migrasi database existing.
-- Periksa tipe data, koneksi, batas indeks, dan foreign key sebelum produksi.


CREATE TABLE data_sources (
	source_id NVARCHAR(120) NOT NULL, 
	title NVARCHAR(500) NOT NULL, 
	publisher NVARCHAR(350) NOT NULL, 
	edition NVARCHAR(120) NULL, 
	uri NTEXT NULL, 
	kind NVARCHAR(30) NOT NULL, 
	license_note NTEXT NULL, 
	PRIMARY KEY (source_id)
)

;


CREATE TABLE employment_contexts (
	context_code NVARCHAR(120) NOT NULL, 
	label_id NVARCHAR(240) NOT NULL, 
	dimension NVARCHAR(120) NOT NULL, 
	PRIMARY KEY (context_code)
)

;


CREATE TABLE riwayat_rilis (
	versi NVARCHAR(120) NOT NULL, 
	hash_manifest NVARCHAR(120) NOT NULL, 
	waktu_rilis DATETIMEOFFSET NOT NULL, 
	status NVARCHAR(120) NOT NULL, 
	PRIMARY KEY (versi)
)

;


CREATE TABLE sectors (
	sector_id NVARCHAR(120) NOT NULL, 
	sector_name NVARCHAR(240) NOT NULL, 
	sector_type NVARCHAR(120) NOT NULL, 
	official_kbli_code NVARCHAR(120) NULL, 
	PRIMARY KEY (sector_id), 
	UNIQUE (sector_name)
)

;


CREATE TABLE kelas_gaji (
	id_kelas_gaji NVARCHAR(120) NOT NULL, 
	sistem_penggajian NVARCHAR(120) NOT NULL, 
	kode_kelas NVARCHAR(120) NOT NULL, 
	nama_kelas NVARCHAR(350) NOT NULL, 
	nilai_dasar_rupiah BIGINT NULL, 
	tahun INTEGER NOT NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	status_verifikasi NVARCHAR(25) NOT NULL, 
	PRIMARY KEY (id_kelas_gaji), 
	UNIQUE (sistem_penggajian, kode_kelas, tahun), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE occupations (
	occupation_id NVARCHAR(120) NOT NULL, 
	preferred_name_id NVARCHAR(350) NOT NULL, 
	alternative_names NTEXT NOT NULL, 
	sector_id NVARCHAR(120) NOT NULL, 
	description_id NTEXT NULL, 
	source_id NVARCHAR(120) NOT NULL, 
	record_status NVARCHAR(25) NOT NULL, 
	last_reviewed DATETIME NULL, 
	PRIMARY KEY (occupation_id), 
	UNIQUE (preferred_name_id, sector_id), 
	FOREIGN KEY(sector_id) REFERENCES sectors (sector_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE riwayat_impor (
	id_impor NVARCHAR(120) NOT NULL, 
	nama_dataset NVARCHAR(120) NOT NULL, 
	versi_dataset NVARCHAR(120) NULL, 
	jumlah_rekaman INTEGER NOT NULL, 
	hash_sha256 NVARCHAR(120) NOT NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	waktu_impor DATETIMEOFFSET NOT NULL, 
	status NVARCHAR(120) NOT NULL, 
	PRIMARY KEY (id_impor), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE wilayah_administratif (
	sistem_kode NVARCHAR(120) NOT NULL, 
	kode_wilayah NVARCHAR(120) NOT NULL, 
	nama_wilayah NVARCHAR(300) NOT NULL, 
	jenis_wilayah NVARCHAR(25) NOT NULL, 
	kode_induk NVARCHAR(120) NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	status_verifikasi NVARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATETIME NULL, 
	PRIMARY KEY (sistem_kode, kode_wilayah), 
	FOREIGN KEY(sistem_kode, kode_induk) REFERENCES wilayah_administratif (sistem_kode, kode_wilayah), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE jabatan_nasional (
	id_jabatan NVARCHAR(120) NOT NULL, 
	nama_jabatan NVARCHAR(350) NOT NULL, 
	id_pekerjaan NVARCHAR(120) NOT NULL, 
	jenis_jabatan NVARCHAR(120) NOT NULL, 
	id_jabatan_induk NVARCHAR(120) NULL, 
	jenjang NVARCHAR(120) NULL, 
	kode_konteks NVARCHAR(120) NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	status_verifikasi NVARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATETIME NULL, 
	catatan NTEXT NULL, 
	PRIMARY KEY (id_jabatan), 
	FOREIGN KEY(id_pekerjaan) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(id_jabatan_induk) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(kode_konteks) REFERENCES employment_contexts (context_code), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE job_titles (
	title_id NVARCHAR(120) NOT NULL, 
	title_name_id NVARCHAR(350) NOT NULL, 
	occupation_id NVARCHAR(120) NOT NULL, 
	seniority_level NVARCHAR(120) NULL, 
	context_code NVARCHAR(120) NULL, 
	notes NTEXT NULL, 
	PRIMARY KEY (title_id), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(context_code) REFERENCES employment_contexts (context_code)
)

;


CREATE TABLE kbji_mappings (
	occupation_id NVARCHAR(120) NOT NULL, 
	kbji_edition NVARCHAR(120) NOT NULL, 
	kbji_code NVARCHAR(12) NOT NULL, 
	kbji_label_id NVARCHAR(350) NOT NULL, 
	source_id NVARCHAR(120) NOT NULL, 
	verified_by NVARCHAR(120) NOT NULL, 
	verified_at DATETIME NOT NULL, 
	PRIMARY KEY (occupation_id, kbji_edition, kbji_code), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE occupation_aliases (
	alias_id BIGINT NOT NULL IDENTITY, 
	occupation_id NVARCHAR(120) NOT NULL, 
	alternative_name_id NVARCHAR(500) NOT NULL, 
	PRIMARY KEY (alias_id), 
	UNIQUE (occupation_id, alternative_name_id), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id)
)

;


CREATE TABLE pemetaan_internasional (
	id_pemetaan NVARCHAR(120) NOT NULL, 
	id_pekerjaan NVARCHAR(120) NOT NULL, 
	sistem_klasifikasi NVARCHAR(120) NOT NULL, 
	edisi NVARCHAR(120) NOT NULL, 
	kode NVARCHAR(120) NOT NULL, 
	nama_resmi NVARCHAR(350) NOT NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	diverifikasi_oleh NVARCHAR(120) NOT NULL, 
	tanggal_verifikasi DATETIME NOT NULL, 
	PRIMARY KEY (id_pemetaan), 
	UNIQUE (id_pekerjaan, sistem_klasifikasi, edisi, kode), 
	FOREIGN KEY(id_pekerjaan) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE upah_minimum (
	id_upah NVARCHAR(120) NOT NULL, 
	sistem_kode NVARCHAR(120) NOT NULL, 
	kode_wilayah NVARCHAR(120) NOT NULL, 
	tahun INTEGER NOT NULL, 
	jenis_upah NVARCHAR(8) NOT NULL, 
	nilai_rupiah BIGINT NOT NULL, 
	tanggal_mulai DATETIME NOT NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	status_verifikasi NVARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATETIME NULL, 
	catatan NTEXT NULL, 
	PRIMARY KEY (id_upah), 
	FOREIGN KEY(sistem_kode, kode_wilayah) REFERENCES wilayah_administratif (sistem_kode, kode_wilayah), 
	UNIQUE (sistem_kode, kode_wilayah, tahun, jenis_upah), 
	CHECK (nilai_rupiah > 0), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE kompetensi_jabatan (
	id_kompetensi NVARCHAR(120) NOT NULL, 
	id_jabatan NVARCHAR(120) NOT NULL, 
	nama_kompetensi NVARCHAR(350) NOT NULL, 
	kategori NVARCHAR(120) NOT NULL, 
	tingkat NVARCHAR(120) NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	status_verifikasi NVARCHAR(25) NOT NULL, 
	PRIMARY KEY (id_kompetensi), 
	FOREIGN KEY(id_jabatan) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE pemetaan_jabatan_kbji (
	id_jabatan NVARCHAR(120) NOT NULL, 
	edisi_kbji NVARCHAR(120) NOT NULL, 
	kode_kbji NVARCHAR(12) NOT NULL, 
	nama_kbji NVARCHAR(350) NOT NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	diverifikasi_oleh NVARCHAR(120) NOT NULL, 
	tanggal_verifikasi DATETIME NOT NULL, 
	PRIMARY KEY (id_jabatan, edisi_kbji, kode_kbji), 
	FOREIGN KEY(id_jabatan) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE statistik_upah (
	id_statistik NVARCHAR(120) NOT NULL, 
	sistem_kode NVARCHAR(120) NOT NULL, 
	kode_wilayah NVARCHAR(120) NOT NULL, 
	tahun INTEGER NOT NULL, 
	id_pekerjaan NVARCHAR(120) NULL, 
	id_jabatan NVARCHAR(120) NULL, 
	metrik NVARCHAR(120) NOT NULL, 
	nilai_rupiah BIGINT NOT NULL, 
	satuan NVARCHAR(120) NOT NULL, 
	cakupan_pekerja NVARCHAR(120) NOT NULL, 
	jenis_data NVARCHAR(120) NOT NULL, 
	jumlah_sampel INTEGER NULL, 
	sumber_id NVARCHAR(120) NOT NULL, 
	status_verifikasi NVARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATETIME NULL, 
	catatan NTEXT NULL, 
	PRIMARY KEY (id_statistik), 
	FOREIGN KEY(sistem_kode, kode_wilayah) REFERENCES wilayah_administratif (sistem_kode, kode_wilayah), 
	CHECK (nilai_rupiah >= 0), 
	FOREIGN KEY(id_pekerjaan) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(id_jabatan) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;

CREATE INDEX idx_pekerjaan_sektor ON occupations (sector_id);
CREATE INDEX idx_jabatan_pekerjaan ON jabatan_nasional (id_pekerjaan);
CREATE INDEX idx_wilayah_induk ON wilayah_administratif (sistem_kode, kode_induk);
CREATE INDEX idx_upah_minimum_wilayah ON upah_minimum (sistem_kode, kode_wilayah, tahun);
CREATE INDEX idx_statistik_upah_wilayah ON statistik_upah (sistem_kode, kode_wilayah, tahun);
