-- RPI 0.4 skema baru oracle. Pratinjau DBA; BUKAN migrasi database existing.
-- Periksa tipe data, koneksi, batas indeks, dan foreign key sebelum produksi.


CREATE TABLE data_sources (
	source_id VARCHAR2(120 CHAR) NOT NULL, 
	title VARCHAR2(500 CHAR) NOT NULL, 
	publisher VARCHAR2(350 CHAR) NOT NULL, 
	edition VARCHAR2(120 CHAR), 
	uri CLOB, 
	kind VARCHAR2(30 CHAR) NOT NULL, 
	license_note CLOB, 
	PRIMARY KEY (source_id)
)

;


CREATE TABLE employment_contexts (
	context_code VARCHAR2(120 CHAR) NOT NULL, 
	label_id VARCHAR2(240 CHAR) NOT NULL, 
	dimension VARCHAR2(120 CHAR) NOT NULL, 
	PRIMARY KEY (context_code)
)

;


CREATE TABLE riwayat_rilis (
	versi VARCHAR2(120 CHAR) NOT NULL, 
	hash_manifest VARCHAR2(120 CHAR) NOT NULL, 
	waktu_rilis DATE NOT NULL, 
	status VARCHAR2(120 CHAR) NOT NULL, 
	PRIMARY KEY (versi)
)

;


CREATE TABLE sectors (
	sector_id VARCHAR2(120 CHAR) NOT NULL, 
	sector_name VARCHAR2(240 CHAR) NOT NULL, 
	sector_type VARCHAR2(120 CHAR) NOT NULL, 
	official_kbli_code VARCHAR2(120 CHAR), 
	PRIMARY KEY (sector_id), 
	UNIQUE (sector_name)
)

;


CREATE TABLE kelas_gaji (
	id_kelas_gaji VARCHAR2(120 CHAR) NOT NULL, 
	sistem_penggajian VARCHAR2(120 CHAR) NOT NULL, 
	kode_kelas VARCHAR2(120 CHAR) NOT NULL, 
	nama_kelas VARCHAR2(350 CHAR) NOT NULL, 
	nilai_dasar_rupiah NUMBER(19), 
	tahun INTEGER NOT NULL, 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	status_verifikasi VARCHAR2(25 CHAR) NOT NULL, 
	PRIMARY KEY (id_kelas_gaji), 
	UNIQUE (sistem_penggajian, kode_kelas, tahun), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE occupations (
	occupation_id VARCHAR2(120 CHAR) NOT NULL, 
	preferred_name_id VARCHAR2(350 CHAR) NOT NULL, 
	alternative_names CLOB NOT NULL, 
	sector_id VARCHAR2(120 CHAR) NOT NULL, 
	description_id CLOB, 
	source_id VARCHAR2(120 CHAR) NOT NULL, 
	record_status VARCHAR2(25 CHAR) NOT NULL, 
	last_reviewed DATE, 
	PRIMARY KEY (occupation_id), 
	UNIQUE (preferred_name_id, sector_id), 
	FOREIGN KEY(sector_id) REFERENCES sectors (sector_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE riwayat_impor (
	id_impor VARCHAR2(120 CHAR) NOT NULL, 
	nama_dataset VARCHAR2(120 CHAR) NOT NULL, 
	versi_dataset VARCHAR2(120 CHAR), 
	jumlah_rekaman INTEGER NOT NULL, 
	hash_sha256 VARCHAR2(120 CHAR) NOT NULL, 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	waktu_impor DATE NOT NULL, 
	status VARCHAR2(120 CHAR) NOT NULL, 
	PRIMARY KEY (id_impor), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE wilayah_administratif (
	sistem_kode VARCHAR2(120 CHAR) NOT NULL, 
	kode_wilayah VARCHAR2(120 CHAR) NOT NULL, 
	nama_wilayah VARCHAR2(300 CHAR) NOT NULL, 
	jenis_wilayah VARCHAR2(25 CHAR) NOT NULL, 
	kode_induk VARCHAR2(120 CHAR), 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	status_verifikasi VARCHAR2(25 CHAR) NOT NULL, 
	tanggal_verifikasi DATE, 
	PRIMARY KEY (sistem_kode, kode_wilayah), 
	FOREIGN KEY(sistem_kode, kode_induk) REFERENCES wilayah_administratif (sistem_kode, kode_wilayah), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE jabatan_nasional (
	id_jabatan VARCHAR2(120 CHAR) NOT NULL, 
	nama_jabatan VARCHAR2(350 CHAR) NOT NULL, 
	id_pekerjaan VARCHAR2(120 CHAR) NOT NULL, 
	jenis_jabatan VARCHAR2(120 CHAR) NOT NULL, 
	id_jabatan_induk VARCHAR2(120 CHAR), 
	jenjang VARCHAR2(120 CHAR), 
	kode_konteks VARCHAR2(120 CHAR), 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	status_verifikasi VARCHAR2(25 CHAR) NOT NULL, 
	tanggal_verifikasi DATE, 
	catatan CLOB, 
	PRIMARY KEY (id_jabatan), 
	FOREIGN KEY(id_pekerjaan) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(id_jabatan_induk) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(kode_konteks) REFERENCES employment_contexts (context_code), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE job_titles (
	title_id VARCHAR2(120 CHAR) NOT NULL, 
	title_name_id VARCHAR2(350 CHAR) NOT NULL, 
	occupation_id VARCHAR2(120 CHAR) NOT NULL, 
	seniority_level VARCHAR2(120 CHAR), 
	context_code VARCHAR2(120 CHAR), 
	notes CLOB, 
	PRIMARY KEY (title_id), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(context_code) REFERENCES employment_contexts (context_code)
)

;


CREATE TABLE kbji_mappings (
	occupation_id VARCHAR2(120 CHAR) NOT NULL, 
	kbji_edition VARCHAR2(120 CHAR) NOT NULL, 
	kbji_code VARCHAR2(12 CHAR) NOT NULL, 
	kbji_label_id VARCHAR2(350 CHAR) NOT NULL, 
	source_id VARCHAR2(120 CHAR) NOT NULL, 
	verified_by VARCHAR2(120 CHAR) NOT NULL, 
	verified_at DATE NOT NULL, 
	PRIMARY KEY (occupation_id, kbji_edition, kbji_code), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE occupation_aliases (
	alias_id NUMBER(19) NOT NULL, 
	occupation_id VARCHAR2(120 CHAR) NOT NULL, 
	alternative_name_id VARCHAR2(500 CHAR) NOT NULL, 
	PRIMARY KEY (alias_id), 
	UNIQUE (occupation_id, alternative_name_id), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id)
)

;


CREATE TABLE pemetaan_internasional (
	id_pemetaan VARCHAR2(120 CHAR) NOT NULL, 
	id_pekerjaan VARCHAR2(120 CHAR) NOT NULL, 
	sistem_klasifikasi VARCHAR2(120 CHAR) NOT NULL, 
	edisi VARCHAR2(120 CHAR) NOT NULL, 
	kode VARCHAR2(120 CHAR) NOT NULL, 
	nama_resmi VARCHAR2(350 CHAR) NOT NULL, 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	diverifikasi_oleh VARCHAR2(120 CHAR) NOT NULL, 
	tanggal_verifikasi DATE NOT NULL, 
	PRIMARY KEY (id_pemetaan), 
	UNIQUE (id_pekerjaan, sistem_klasifikasi, edisi, kode), 
	FOREIGN KEY(id_pekerjaan) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE upah_minimum (
	id_upah VARCHAR2(120 CHAR) NOT NULL, 
	sistem_kode VARCHAR2(120 CHAR) NOT NULL, 
	kode_wilayah VARCHAR2(120 CHAR) NOT NULL, 
	tahun INTEGER NOT NULL, 
	jenis_upah VARCHAR2(8 CHAR) NOT NULL, 
	nilai_rupiah NUMBER(19) NOT NULL, 
	tanggal_mulai DATE NOT NULL, 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	status_verifikasi VARCHAR2(25 CHAR) NOT NULL, 
	tanggal_verifikasi DATE, 
	catatan CLOB, 
	PRIMARY KEY (id_upah), 
	FOREIGN KEY(sistem_kode, kode_wilayah) REFERENCES wilayah_administratif (sistem_kode, kode_wilayah), 
	UNIQUE (sistem_kode, kode_wilayah, tahun, jenis_upah), 
	CHECK (nilai_rupiah > 0), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE kompetensi_jabatan (
	id_kompetensi VARCHAR2(120 CHAR) NOT NULL, 
	id_jabatan VARCHAR2(120 CHAR) NOT NULL, 
	nama_kompetensi VARCHAR2(350 CHAR) NOT NULL, 
	kategori VARCHAR2(120 CHAR) NOT NULL, 
	tingkat VARCHAR2(120 CHAR), 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	status_verifikasi VARCHAR2(25 CHAR) NOT NULL, 
	PRIMARY KEY (id_kompetensi), 
	FOREIGN KEY(id_jabatan) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE pemetaan_jabatan_kbji (
	id_jabatan VARCHAR2(120 CHAR) NOT NULL, 
	edisi_kbji VARCHAR2(120 CHAR) NOT NULL, 
	kode_kbji VARCHAR2(12 CHAR) NOT NULL, 
	nama_kbji VARCHAR2(350 CHAR) NOT NULL, 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	diverifikasi_oleh VARCHAR2(120 CHAR) NOT NULL, 
	tanggal_verifikasi DATE NOT NULL, 
	PRIMARY KEY (id_jabatan, edisi_kbji, kode_kbji), 
	FOREIGN KEY(id_jabatan) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE statistik_upah (
	id_statistik VARCHAR2(120 CHAR) NOT NULL, 
	sistem_kode VARCHAR2(120 CHAR) NOT NULL, 
	kode_wilayah VARCHAR2(120 CHAR) NOT NULL, 
	tahun INTEGER NOT NULL, 
	id_pekerjaan VARCHAR2(120 CHAR), 
	id_jabatan VARCHAR2(120 CHAR), 
	metrik VARCHAR2(120 CHAR) NOT NULL, 
	nilai_rupiah NUMBER(19) NOT NULL, 
	satuan VARCHAR2(120 CHAR) NOT NULL, 
	cakupan_pekerja VARCHAR2(120 CHAR) NOT NULL, 
	jenis_data VARCHAR2(120 CHAR) NOT NULL, 
	jumlah_sampel INTEGER, 
	sumber_id VARCHAR2(120 CHAR) NOT NULL, 
	status_verifikasi VARCHAR2(25 CHAR) NOT NULL, 
	tanggal_verifikasi DATE, 
	catatan CLOB, 
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
