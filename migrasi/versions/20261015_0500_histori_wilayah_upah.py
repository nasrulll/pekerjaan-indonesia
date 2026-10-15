"""Tabel historis aditif RPI v0.5.0.

Tidak menghapus atau menulis ulang wilayah_administratif dan upah_minimum
yang telah dipakai pada v0.4.0. Downgrade otomatis sengaja dinonaktifkan.
"""
from alembic import op
from nor_id.skema_histori import metadata_histori, sumber, wilayah, keputusan

revision = "20261015_0500"
down_revision = "20261015_0400"
branch_labels = None
depends_on = None


def upgrade():
    # create_all(checkfirst) aman ketika migrasi awal v0.4 dijalankan bersama
    # tabel baru, dan mencegah upaya membuat tabel yang sudah tersedia.
    bind = op.get_bind()
    metadata_histori.create_all(bind, tables=[sumber, wilayah, keputusan], checkfirst=True)


def downgrade():
    raise RuntimeError(
        "Rollback destruktif tabel historis tidak otomatis; simpan cadangan "
        "dan jalankan migrasi balik yang ditinjau terlebih dahulu."
    )
