"""Tabel taksonomi KBJI berversi; data impor hanya berstatus ditinjau."""
from alembic import op
from nor_id.skema_histori import metadata_histori, taksonomi_kbji

revision = "20261015_0600"
down_revision = "20261015_0500"
branch_labels = None
depends_on = None

def upgrade():
    metadata_histori.create_all(
        op.get_bind(), tables=[taksonomi_kbji], checkfirst=True
    )

def downgrade():
    raise RuntimeError("Rollback destruktif harus melalui cadangan dan tinjauan")
