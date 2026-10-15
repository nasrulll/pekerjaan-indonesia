"""Migrasi RPI: URL dari lingkungan, migrasi destruktif tidak otomatis."""
import os
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
from nor_id.basis_data import periksa_url
from nor_id.skema_portabel import metadata

config=context.config
url=os.environ.get('RPI_DATABASE_URL')
if not url:
    raise RuntimeError('RPI_DATABASE_URL wajib saat menjalankan Alembic')
periksa_url(url,periksa_berkas=False)
config.set_main_option('sqlalchemy.url',url.replace('%','%%'))

def offline():
    context.configure(url=url,target_metadata=metadata,literal_binds=True,compare_type=True)
    with context.begin_transaction(): context.run_migrations()

def online():
    engine=engine_from_config(config.get_section(config.config_ini_section),
                              prefix='sqlalchemy.',poolclass=pool.NullPool)
    with engine.connect() as connection:
        context.configure(connection=connection,target_metadata=metadata,compare_type=True)
        with context.begin_transaction(): context.run_migrations()
    engine.dispose()

if context.is_offline_mode(): offline()
else: online()
