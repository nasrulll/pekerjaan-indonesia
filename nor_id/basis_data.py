"""Koneksi basis data yang diizinkan. Tidak ada akses jaringan saat impor modul."""
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url

PENGGERAK = {
    'sqlite': ('pysqlite', 'SQLite'),
    'postgresql': ('psycopg', 'PostgreSQL'),
    'mysql': ('pymysql', 'MySQL'),
    'mariadb': ('pymysql', 'MariaDB'),
    'mssql': ('pyodbc', 'Microsoft SQL Server'),
    'oracle': ('oracledb', 'Oracle Database'),
}

def periksa_url(url: str, *, periksa_berkas: bool = True):
    """Periksa dialect+driver tanpa membuka koneksi; kredensial tidak ditulis ke log."""
    alamat = make_url(url)
    nama = alamat.get_backend_name()
    if nama not in PENGGERAK:
        raise ValueError("Dialek basis data tidak didukung")
    driver = alamat.get_driver_name()
    if driver != PENGGERAK[nama][0]:
        raise ValueError('Gunakan dialect+driver yang didukung: ' + ', '.join(
            f'{dialect}+{d[0]}' for dialect, d in PENGGERAK.items()))
    if nama == 'sqlite' and periksa_berkas and alamat.database not in (None, ':memory:'):
        if not Path(alamat.database).is_file():
            raise RuntimeError('Berkas SQLite belum tersedia. Bangun paket SQLite lebih dahulu.')
    return alamat

def buat_mesin(url: str, *, periksa_berkas: bool = True):
    alamat = periksa_url(url, periksa_berkas=periksa_berkas)
    tambahan = {'check_same_thread': False} if alamat.get_backend_name() == 'sqlite' else {}
    return create_engine(alamat, connect_args=tambahan, pool_pre_ping=True)

def sql_berhalaman(conn, sql: str) -> str:
    """SQL pagination terkendali: bind parameter; SQL Server dan Oracle butuh OFFSET/FETCH."""
    if conn.dialect.name in ('mssql', 'oracle'):
        return sql + ' OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY'
    return sql + ' LIMIT :limit OFFSET :offset'
