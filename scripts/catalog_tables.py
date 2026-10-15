"""Allowed SQL identifier column names for catalog ingestion."""
# Fixed column names prevent a modified CSV header from being interpreted as SQL.
COLUMNS = {
    "data_sources": ("source_id", "title", "publisher", "edition", "uri", "kind", "license_note"),
    "sectors": ("sector_id", "sector_name", "sector_type", "official_kbli_code"),
    "occupations": ("occupation_id", "preferred_name_id", "alternative_names", "sector_id",
                    "description_id", "source_id", "record_status", "last_reviewed"),
    "employment_contexts": ("context_code", "label_id", "dimension"),
    "job_titles": ("title_id", "title_name_id", "occupation_id", "seniority_level", "context_code", "notes"),
    "kbji_mappings": ("occupation_id", "kbji_edition", "kbji_code", "kbji_label_id",
                       "source_id", "verified_by", "verified_at"),
    "jabatan_nasional": ("id_jabatan","nama_jabatan","id_pekerjaan","jenis_jabatan","id_jabatan_induk","jenjang","kode_konteks","sumber_id","status_verifikasi","tanggal_verifikasi","catatan"),
    "wilayah_administratif": ("sistem_kode","kode_wilayah","nama_wilayah","jenis_wilayah","kode_induk","sumber_id","status_verifikasi","tanggal_verifikasi"),
    "pemetaan_jabatan_kbji": ("id_jabatan","edisi_kbji","kode_kbji","nama_kbji","sumber_id","diverifikasi_oleh","tanggal_verifikasi"),
    "kompetensi_jabatan": ("id_kompetensi","id_jabatan","nama_kompetensi","kategori","tingkat","sumber_id","status_verifikasi"),
    "upah_minimum": ("id_upah","sistem_kode","kode_wilayah","tahun","jenis_upah","nilai_rupiah","tanggal_mulai","sumber_id","status_verifikasi","tanggal_verifikasi","catatan"),
    "statistik_upah": ("id_statistik","sistem_kode","kode_wilayah","tahun","id_pekerjaan","id_jabatan","metrik","nilai_rupiah","satuan","cakupan_pekerja","jenis_data","jumlah_sampel","sumber_id","status_verifikasi","tanggal_verifikasi","catatan"),
    "kelas_gaji": ("id_kelas_gaji","sistem_penggajian","kode_kelas","nama_kelas","nilai_dasar_rupiah","tahun","sumber_id","status_verifikasi"),
}

