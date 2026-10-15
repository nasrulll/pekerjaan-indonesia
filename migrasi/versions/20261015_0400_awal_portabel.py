"""Inisialisasi basis data baru dan kosong dengan skema portabel RPI.

Jangan gunakan pada database v0.3 yang sudah ada. Untuk upgrade v0.3
terlebih dahulu jalankan migrasi SQL spesifik yang direview manusia.
"""
from alembic import op
from sqlalchemy import inspect
from nor_id.skema_portabel import metadata

revision='20261015_0400'
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    bind=op.get_bind()
    existing=[n for n in inspect(bind).get_table_names() if n!='alembic_version']
    if existing:
        raise RuntimeError('Migrasi awal hanya untuk database kosong. Gunakan migrasi v0.3→v0.4 yang terpisah.')
    metadata.create_all(bind)

def downgrade():
    raise RuntimeError('Rollback destruktif dilarang otomatis. Pulihkan backup jika perlu.')
