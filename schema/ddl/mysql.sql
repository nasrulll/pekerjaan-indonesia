-- RPI 0.4 skema baru mysql. Pratinjau DBA; BUKAN migrasi database existing.
-- Periksa tipe data, koneksi, batas indeks, dan foreign key sebelum produksi.


CREATE TABLE data_sources (
	source_id VARCHAR(120) NOT NULL, 
	title VARCHAR(500) NOT NULL, 
	publisher VARCHAR(350) NOT NULL, 
	edition VARCHAR(120), 
	uri TEXT, 
	kind VARCHAR(30) NOT NULL, 
	license_note TEXT, 
	PRIMARY KEY (source_id)
)

;


CREATE TABLE employment_contexts (
	context_code VARCHAR(120) NOT NULL, 
	label_id VARCHAR(240) NOT NULL, 
	dimension VARCHAR(120) NOT NULL, 
	PRIMARY KEY (context_code)
)

;


CREATE TABLE riwayat_rilis (
	versi VARCHAR(120) NOT NULL, 
	hash_manifest VARCHAR(120) NOT NULL, 
	waktu_rilis DATETIME NOT NULL, 
	status VARCHAR(120) NOT NULL, 
	PRIMARY KEY (versi)
)

;


CREATE TABLE sectors (
	sector_id VARCHAR(120) NOT NULL, 
	sector_name VARCHAR(240) NOT NULL, 
	sector_type VARCHAR(120) NOT NULL, 
	official_kbli_code VARCHAR(120), 
	PRIMARY KEY (sector_id), 
	UNIQUE (sector_name)
)

;


CREATE TABLE kelas_gaji (
	id_kelas_gaji VARCHAR(120) NOT NULL, 
	sistem_penggajian VARCHAR(120) NOT NULL, 
	kode_kelas VARCHAR(120) NOT NULL, 
	nama_kelas VARCHAR(350) NOT NULL, 
	nilai_dasar_rupiah BIGINT, 
	tahun INTEGER NOT NULL, 
	sumber_id VARCHAR(120) NOT NULL, 
	status_verifikasi VARCHAR(25) NOT NULL, 
	PRIMARY KEY (id_kelas_gaji), 
	UNIQUE (sistem_penggajian, kode_kelas, tahun), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE occupations (
	occupation_id VARCHAR(120) NOT NULL, 
	preferred_name_id VARCHAR(350) NOT NULL, 
	alternative_names TEXT NOT NULL, 
	sector_id VARCHAR(120) NOT NULL, 
	description_id TEXT, 
	source_id VARCHAR(120) NOT NULL, 
	record_status VARCHAR(25) NOT NULL, 
	last_reviewed DATE, 
	PRIMARY KEY (occupation_id), 
	UNIQUE (preferred_name_id, sector_id), 
	FOREIGN KEY(sector_id) REFERENCES sectors (sector_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE riwayat_impor (
	id_impor VARCHAR(120) NOT NULL, 
	nama_dataset VARCHAR(120) NOT NULL, 
	versi_dataset VARCHAR(120), 
	jumlah_rekaman INTEGER NOT NULL, 
	hash_sha256 VARCHAR(120) NOT NULL, 
	sumber_id VARCHAR(120) NOT NULL, 
	waktu_impor DATETIME NOT NULL, 
	status VARCHAR(120) NOT NULL, 
	PRIMARY KEY (id_impor), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE wilayah_administratif (
	sistem_kode VARCHAR(120) NOT NULL, 
	kode_wilayah VARCHAR(120) NOT NULL, 
	nama_wilayah VARCHAR(300) NOT NULL, 
	jenis_wilayah VARCHAR(25) NOT NULL, 
	kode_induk VARCHAR(120), 
	sumber_id VARCHAR(120) NOT NULL, 
	status_verifikasi VARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATE, 
	PRIMARY KEY (sistem_kode, kode_wilayah), 
	FOREIGN KEY(sistem_kode, kode_induk) REFERENCES wilayah_administratif (sistem_kode, kode_wilayah), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE jabatan_nasional (
	id_jabatan VARCHAR(120) NOT NULL, 
	nama_jabatan VARCHAR(350) NOT NULL, 
	id_pekerjaan VARCHAR(120) NOT NULL, 
	jenis_jabatan VARCHAR(120) NOT NULL, 
	id_jabatan_induk VARCHAR(120), 
	jenjang VARCHAR(120), 
	kode_konteks VARCHAR(120), 
	sumber_id VARCHAR(120) NOT NULL, 
	status_verifikasi VARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATE, 
	catatan TEXT, 
	PRIMARY KEY (id_jabatan), 
	FOREIGN KEY(id_pekerjaan) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(id_jabatan_induk) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(kode_konteks) REFERENCES employment_contexts (context_code), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE job_titles (
	title_id VARCHAR(120) NOT NULL, 
	title_name_id VARCHAR(350) NOT NULL, 
	occupation_id VARCHAR(120) NOT NULL, 
	seniority_level VARCHAR(120), 
	context_code VARCHAR(120), 
	notes TEXT, 
	PRIMARY KEY (title_id), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(context_code) REFERENCES employment_contexts (context_code)
)

;


CREATE TABLE kbji_mappings (
	occupation_id VARCHAR(120) NOT NULL, 
	kbji_edition VARCHAR(120) NOT NULL, 
	kbji_code VARCHAR(12) NOT NULL, 
	kbji_label_id VARCHAR(350) NOT NULL, 
	source_id VARCHAR(120) NOT NULL, 
	verified_by VARCHAR(120) NOT NULL, 
	verified_at DATE NOT NULL, 
	PRIMARY KEY (occupation_id, kbji_edition, kbji_code), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(source_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE occupation_aliases (
	alias_id BIGINT NOT NULL AUTO_INCREMENT, 
	occupation_id VARCHAR(120) NOT NULL, 
	alternative_name_id VARCHAR(500) NOT NULL, 
	PRIMARY KEY (alias_id), 
	UNIQUE (occupation_id, alternative_name_id), 
	FOREIGN KEY(occupation_id) REFERENCES occupations (occupation_id)
)

;


CREATE TABLE pemetaan_internasional (
	id_pemetaan VARCHAR(120) NOT NULL, 
	id_pekerjaan VARCHAR(120) NOT NULL, 
	sistem_klasifikasi VARCHAR(120) NOT NULL, 
	edisi VARCHAR(120) NOT NULL, 
	kode VARCHAR(120) NOT NULL, 
	nama_resmi VARCHAR(350) NOT NULL, 
	sumber_id VARCHAR(120) NOT NULL, 
	diverifikasi_oleh VARCHAR(120) NOT NULL, 
	tanggal_verifikasi DATE NOT NULL, 
	PRIMARY KEY (id_pemetaan), 
	UNIQUE (id_pekerjaan, sistem_klasifikasi, edisi, kode), 
	FOREIGN KEY(id_pekerjaan) REFERENCES occupations (occupation_id), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE upah_minimum (
	id_upah VARCHAR(120) NOT NULL, 
	sistem_kode VARCHAR(120) NOT NULL, 
	kode_wilayah VARCHAR(120) NOT NULL, 
	tahun INTEGER NOT NULL, 
	jenis_upah VARCHAR(8) NOT NULL, 
	nilai_rupiah BIGINT NOT NULL, 
	tanggal_mulai DATE NOT NULL, 
	sumber_id VARCHAR(120) NOT NULL, 
	status_verifikasi VARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATE, 
	catatan TEXT, 
	PRIMARY KEY (id_upah), 
	FOREIGN KEY(sistem_kode, kode_wilayah) REFERENCES wilayah_administratif (sistem_kode, kode_wilayah), 
	UNIQUE (sistem_kode, kode_wilayah, tahun, jenis_upah), 
	CHECK (nilai_rupiah > 0), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE kompetensi_jabatan (
	id_kompetensi VARCHAR(120) NOT NULL, 
	id_jabatan VARCHAR(120) NOT NULL, 
	nama_kompetensi VARCHAR(350) NOT NULL, 
	kategori VARCHAR(120) NOT NULL, 
	tingkat VARCHAR(120), 
	sumber_id VARCHAR(120) NOT NULL, 
	status_verifikasi VARCHAR(25) NOT NULL, 
	PRIMARY KEY (id_kompetensi), 
	FOREIGN KEY(id_jabatan) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE pemetaan_jabatan_kbji (
	id_jabatan VARCHAR(120) NOT NULL, 
	edisi_kbji VARCHAR(120) NOT NULL, 
	kode_kbji VARCHAR(12) NOT NULL, 
	nama_kbji VARCHAR(350) NOT NULL, 
	sumber_id VARCHAR(120) NOT NULL, 
	diverifikasi_oleh VARCHAR(120) NOT NULL, 
	tanggal_verifikasi DATE NOT NULL, 
	PRIMARY KEY (id_jabatan, edisi_kbji, kode_kbji), 
	FOREIGN KEY(id_jabatan) REFERENCES jabatan_nasional (id_jabatan), 
	FOREIGN KEY(sumber_id) REFERENCES data_sources (source_id)
)

;


CREATE TABLE statistik_upah (
	id_statistik VARCHAR(120) NOT NULL, 
	sistem_kode VARCHAR(120) NOT NULL, 
	kode_wilayah VARCHAR(120) NOT NULL, 
	tahun INTEGER NOT NULL, 
	id_pekerjaan VARCHAR(120), 
	id_jabatan VARCHAR(120), 
	metrik VARCHAR(120) NOT NULL, 
	nilai_rupiah BIGINT NOT NULL, 
	satuan VARCHAR(120) NOT NULL, 
	cakupan_pekerja VARCHAR(120) NOT NULL, 
	jenis_data VARCHAR(120) NOT NULL, 
	jumlah_sampel INTEGER, 
	sumber_id VARCHAR(120) NOT NULL, 
	status_verifikasi VARCHAR(25) NOT NULL, 
	tanggal_verifikasi DATE, 
	catatan TEXT, 
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
