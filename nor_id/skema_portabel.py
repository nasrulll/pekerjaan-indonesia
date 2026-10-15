"""DDL portabel SQLAlchemy untuk instalasi basis data baru (bukan auto-migrasi destruktif).

SQLAlchemy menerjemahkan tipe TEXT/Unicode, identitas, FK, unique, tanggal, integer
ke PostgreSQL, SQLite, MySQL/MariaDB, SQL Server dan Oracle. Untuk DB lama,
jalankan migrasi review manual sebelum menjalankan pemuatan data.
"""
from sqlalchemy import (MetaData, Table, Column, String, Unicode, UnicodeText,
                        BigInteger, Integer, Date, DateTime, ForeignKey,
                        ForeignKeyConstraint, UniqueConstraint, CheckConstraint,
                        Index, text)

metadata = MetaData()

def txt(n, *, pk=False, nullable=True, panjang=120):
    return Column(n, Unicode(panjang), primary_key=pk, nullable=False if pk else nullable)

def isi(n, *, nullable=True):
    return Column(n, UnicodeText(), nullable=nullable)

def ref(n, tabel, kolom, *, nullable=False):
    return Column(n, Unicode(120), ForeignKey(f'{tabel}.{kolom}'), nullable=nullable)

def nomor(n, *, nullable=False):
    return Column(n, BigInteger, nullable=nullable)

def status_verifikasi():
    return txt('status_verifikasi', nullable=False, panjang=25)

Table('data_sources', metadata,
      txt('source_id',pk=True), txt('title',nullable=False,panjang=500),
      txt('publisher',nullable=False,panjang=350),txt('edition'), isi('uri'),
      txt('kind',nullable=False,panjang=30),isi('license_note'))
Table('sectors',metadata,txt('sector_id',pk=True),txt('sector_name',nullable=False,panjang=240),
      txt('sector_type',nullable=False),txt('official_kbli_code'),UniqueConstraint('sector_name'))
Table('occupations',metadata,txt('occupation_id',pk=True),txt('preferred_name_id',nullable=False,panjang=350),
      isi('alternative_names',nullable=False),ref('sector_id','sectors','sector_id'),isi('description_id'),
      ref('source_id','data_sources','source_id'),txt('record_status',nullable=False,panjang=25),
      Column('last_reviewed',Date), UniqueConstraint('preferred_name_id','sector_id'))
Table('occupation_aliases',metadata,
      Column('alias_id',BigInteger().with_variant(Integer,'sqlite'),primary_key=True,autoincrement=True),
      ref('occupation_id','occupations','occupation_id'),txt('alternative_name_id',nullable=False,panjang=500),
      UniqueConstraint('occupation_id','alternative_name_id'))
Table('kbji_mappings',metadata,ref('occupation_id','occupations','occupation_id'),
      txt('kbji_edition',nullable=False),txt('kbji_code',nullable=False,panjang=12),
      txt('kbji_label_id',nullable=False,panjang=350),ref('source_id','data_sources','source_id'),
      txt('verified_by',nullable=False),Column('verified_at',Date,nullable=False),
      # Composite PK set after definition below.
      )
metadata.tables['kbji_mappings'].append_constraint(
    __import__('sqlalchemy').PrimaryKeyConstraint('occupation_id','kbji_edition','kbji_code'))
Table('employment_contexts',metadata,txt('context_code',pk=True),
      txt('label_id',nullable=False,panjang=240),txt('dimension',nullable=False))
Table('job_titles',metadata,txt('title_id',pk=True),txt('title_name_id',nullable=False,panjang=350),
      ref('occupation_id','occupations','occupation_id'),txt('seniority_level'),
      ref('context_code','employment_contexts','context_code',nullable=True),isi('notes'))
Table('jabatan_nasional',metadata,txt('id_jabatan',pk=True),txt('nama_jabatan',nullable=False,panjang=350),
      ref('id_pekerjaan','occupations','occupation_id'),txt('jenis_jabatan',nullable=False),
      ref('id_jabatan_induk','jabatan_nasional','id_jabatan',nullable=True),txt('jenjang'),
      ref('kode_konteks','employment_contexts','context_code',nullable=True),
      ref('sumber_id','data_sources','source_id'),status_verifikasi(),
      Column('tanggal_verifikasi',Date),isi('catatan'))
Table('wilayah_administratif',metadata,txt('sistem_kode',pk=True),txt('kode_wilayah',pk=True),
      txt('nama_wilayah',nullable=False,panjang=300),txt('jenis_wilayah',nullable=False,panjang=25),
      txt('kode_induk'),ref('sumber_id','data_sources','source_id'),status_verifikasi(),
      Column('tanggal_verifikasi',Date),
      ForeignKeyConstraint(['sistem_kode','kode_induk'],['wilayah_administratif.sistem_kode','wilayah_administratif.kode_wilayah']))
Table('pemetaan_jabatan_kbji',metadata,ref('id_jabatan','jabatan_nasional','id_jabatan'),
      txt('edisi_kbji',nullable=False),txt('kode_kbji',nullable=False,panjang=12),
      txt('nama_kbji',nullable=False,panjang=350),ref('sumber_id','data_sources','source_id'),
      txt('diverifikasi_oleh',nullable=False),Column('tanggal_verifikasi',Date,nullable=False),
      __import__('sqlalchemy').PrimaryKeyConstraint('id_jabatan','edisi_kbji','kode_kbji'))
Table('kompetensi_jabatan',metadata,txt('id_kompetensi',pk=True),
      ref('id_jabatan','jabatan_nasional','id_jabatan'),txt('nama_kompetensi',nullable=False,panjang=350),
      txt('kategori',nullable=False),txt('tingkat'),ref('sumber_id','data_sources','source_id'),status_verifikasi())
Table('upah_minimum',metadata,txt('id_upah',pk=True),txt('sistem_kode',nullable=False),
      txt('kode_wilayah',nullable=False),Column('tahun',Integer,nullable=False),
      txt('jenis_upah',nullable=False,panjang=8),nomor('nilai_rupiah'),
      Column('tanggal_mulai',Date,nullable=False),ref('sumber_id','data_sources','source_id'),
      status_verifikasi(),Column('tanggal_verifikasi',Date),isi('catatan'),
      ForeignKeyConstraint(['sistem_kode','kode_wilayah'],['wilayah_administratif.sistem_kode','wilayah_administratif.kode_wilayah']),
      UniqueConstraint('sistem_kode','kode_wilayah','tahun','jenis_upah'),CheckConstraint('nilai_rupiah > 0'))
Table('statistik_upah',metadata,txt('id_statistik',pk=True),txt('sistem_kode',nullable=False),
      txt('kode_wilayah',nullable=False),Column('tahun',Integer,nullable=False),
      ref('id_pekerjaan','occupations','occupation_id',nullable=True),
      ref('id_jabatan','jabatan_nasional','id_jabatan',nullable=True),
      txt('metrik',nullable=False),nomor('nilai_rupiah'),txt('satuan',nullable=False),
      txt('cakupan_pekerja',nullable=False),txt('jenis_data',nullable=False),
      Column('jumlah_sampel',Integer),ref('sumber_id','data_sources','source_id'),
      status_verifikasi(),Column('tanggal_verifikasi',Date),isi('catatan'),
      ForeignKeyConstraint(['sistem_kode','kode_wilayah'],['wilayah_administratif.sistem_kode','wilayah_administratif.kode_wilayah']),
      CheckConstraint('nilai_rupiah >= 0'))
Table('kelas_gaji',metadata,txt('id_kelas_gaji',pk=True),txt('sistem_penggajian',nullable=False),
      txt('kode_kelas',nullable=False),txt('nama_kelas',nullable=False,panjang=350),
      nomor('nilai_dasar_rupiah',nullable=True),Column('tahun',Integer,nullable=False),
      ref('sumber_id','data_sources','source_id'),status_verifikasi(),
      UniqueConstraint('sistem_penggajian','kode_kelas','tahun'))
Table('riwayat_impor',metadata,txt('id_impor',pk=True),txt('nama_dataset',nullable=False),
      txt('versi_dataset'),Column('jumlah_rekaman',Integer,nullable=False),
      txt('hash_sha256',nullable=False),ref('sumber_id','data_sources','source_id'),
      Column('waktu_impor',DateTime(timezone=True),nullable=False),txt('status',nullable=False))
Table('pemetaan_internasional',metadata,
      txt('id_pemetaan',pk=True), ref('id_pekerjaan','occupations','occupation_id'),
      txt('sistem_klasifikasi',nullable=False),txt('edisi',nullable=False),
      txt('kode',nullable=False),txt('nama_resmi',nullable=False,panjang=350),
      ref('sumber_id','data_sources','source_id'),txt('diverifikasi_oleh',nullable=False),
      Column('tanggal_verifikasi',Date,nullable=False),UniqueConstraint('id_pekerjaan','sistem_klasifikasi','edisi','kode'))
Table('riwayat_rilis',metadata,txt('versi',pk=True),txt('hash_manifest',nullable=False),
      Column('waktu_rilis',DateTime(timezone=True),nullable=False),txt('status',nullable=False))

Index('idx_pekerjaan_sektor',metadata.tables['occupations'].c.sector_id)
Index('idx_jabatan_pekerjaan',metadata.tables['jabatan_nasional'].c.id_pekerjaan)
Index('idx_wilayah_induk',metadata.tables['wilayah_administratif'].c.sistem_kode,
      metadata.tables['wilayah_administratif'].c.kode_induk)
Index('idx_upah_minimum_wilayah',metadata.tables['upah_minimum'].c.sistem_kode,
      metadata.tables['upah_minimum'].c.kode_wilayah,metadata.tables['upah_minimum'].c.tahun)
Index('idx_statistik_upah_wilayah',metadata.tables['statistik_upah'].c.sistem_kode,
      metadata.tables['statistik_upah'].c.kode_wilayah,metadata.tables['statistik_upah'].c.tahun)
