"""Skema historis RPI v0.5: aditif, bukan perubahan tabel publik v0.4.

Rujukan sumber, wilayah berdasarkan edisi, dan keputusan pengupahan historis.
Isi dan status "terverifikasi" hanya melalui proses tinjauan manusia.
"""
from sqlalchemy import (
    MetaData, Table, Column, Unicode, Integer, BigInteger, Date,
    ForeignKey, ForeignKeyConstraint, PrimaryKeyConstraint,
    UniqueConstraint, CheckConstraint, Index,
)

metadata_histori = MetaData()

sumber = Table(
    "sumber_publikasi", metadata_histori,
    Column("id_sumber", Unicode(120), primary_key=True),
    Column("jenis_sumber", Unicode(40), nullable=False),
    Column("penerbit", Unicode(250), nullable=False),
    Column("judul", Unicode(500), nullable=False),
    Column("edisi", Unicode(80), nullable=False),
    Column("url_resmi", Unicode(850), nullable=False),
    Column("sha256_berkas_asli", Unicode(64), nullable=False),
    Column("izin_distribusi", Unicode(25), nullable=False),
    Column("rujukan_izin", Unicode(850)),
    Column("status_verifikasi", Unicode(24), nullable=False),
    Column("peninjau", Unicode(150)),
    Column("tanggal_verifikasi", Date),
    CheckConstraint(
        "status_verifikasi IN ('draf','ditinjau','terverifikasi')",
        name="ck_sumber_publikasi_status",
    ),
    CheckConstraint(
        "izin_distribusi IN ('diizinkan','dilarang','belum_diperiksa')",
        name="ck_sumber_publikasi_izin",
    ),
)

wilayah = Table(
    "wilayah_per_edisi", metadata_histori,
    Column("sistem_kode", Unicode(40), nullable=False),
    Column("edisi", Unicode(80), nullable=False),
    Column("kode_wilayah", Unicode(48), nullable=False),
    Column("nama_wilayah", Unicode(300), nullable=False),
    Column("jenis_wilayah", Unicode(20), nullable=False),
    Column("kode_induk", Unicode(48), nullable=True),
    Column("id_sumber", Unicode(120), ForeignKey("sumber_publikasi.id_sumber"), nullable=False),
    Column("status_verifikasi", Unicode(24), nullable=False),
    PrimaryKeyConstraint("sistem_kode", "edisi", "kode_wilayah", name="pk_wilayah_per_edisi"),
    ForeignKeyConstraint(
        ["sistem_kode", "edisi", "kode_induk"],
        ["wilayah_per_edisi.sistem_kode", "wilayah_per_edisi.edisi", "wilayah_per_edisi.kode_wilayah"],
        name="fk_wilayah_per_edisi_induk",
    ),
    CheckConstraint(
        "jenis_wilayah IN ('provinsi','kabupaten','kota')",
        name="ck_wilayah_per_edisi_jenis",
    ),
    CheckConstraint(
        "status_verifikasi IN ('draf','ditinjau','terverifikasi')",
        name="ck_wilayah_per_edisi_status",
    ),
)

keputusan = Table(
    "keputusan_upah_historis", metadata_histori,
    Column("id_keputusan", Unicode(120), primary_key=True),
    Column("sistem_kode", Unicode(40), nullable=False),
    Column("edisi_wilayah", Unicode(80), nullable=False),
    Column("kode_wilayah", Unicode(48), nullable=False),
    Column("tahun", Integer, nullable=False),
    Column("jenis_upah", Unicode(3), nullable=False),
    Column("nilai_rupiah", BigInteger, nullable=False),
    Column("tanggal_mulai", Date, nullable=False),
    Column("nomor_keputusan", Unicode(220), nullable=False),
    Column("tanggal_keputusan", Date, nullable=False),
    Column("status_keputusan", Unicode(14), nullable=False),
    Column("id_keputusan_digantikan", Unicode(120), ForeignKey("keputusan_upah_historis.id_keputusan")),
    Column("id_sumber", Unicode(120), ForeignKey("sumber_publikasi.id_sumber"), nullable=False),
    Column("status_verifikasi", Unicode(24), nullable=False),
    ForeignKeyConstraint(
        ["sistem_kode", "edisi_wilayah", "kode_wilayah"],
        ["wilayah_per_edisi.sistem_kode", "wilayah_per_edisi.edisi", "wilayah_per_edisi.kode_wilayah"],
        name="fk_keputusan_wilayah_edisi",
    ),
    UniqueConstraint(
        "sistem_kode", "edisi_wilayah", "kode_wilayah", "tahun",
        "jenis_upah", "nomor_keputusan", name="uq_keputusan_upah_natural",
    ),
    CheckConstraint("nilai_rupiah > 0", name="ck_keputusan_nilai_positif"),
    CheckConstraint("tahun BETWEEN 1900 AND 2200", name="ck_keputusan_tahun"),
    CheckConstraint("jenis_upah IN ('UMP','UMK')", name="ck_keputusan_jenis"),
    CheckConstraint(
        "status_keputusan IN ('berlaku','diganti','dicabut')",
        name="ck_keputusan_status",
    ),
    CheckConstraint(
        "status_verifikasi IN ('draf','ditinjau','terverifikasi')",
        name="ck_keputusan_verifikasi",
    ),
)

Index("idx_keputusan_wilayah_tahun", keputusan.c.sistem_kode,
      keputusan.c.edisi_wilayah, keputusan.c.kode_wilayah, keputusan.c.tahun)
