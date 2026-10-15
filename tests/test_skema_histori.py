"""Uji skema historis. Data contoh SINTETIS dan tidak dianggap resmi."""
import unittest
from datetime import date

from sqlalchemy import create_engine, event, insert, select, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects import postgresql, mysql, mssql, oracle, sqlite
from sqlalchemy.schema import CreateTable

from nor_id.skema_histori import metadata_histori


class TestSkemaHistoris(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite+pysqlite:///:memory:")
        @event.listens_for(self.engine, "connect")
        def _fk(dbapi, _):
            dbapi.execute("PRAGMA foreign_keys=ON")
        metadata_histori.create_all(self.engine)
        self.sumber = metadata_histori.tables["sumber_publikasi"]
        self.wilayah = metadata_histori.tables["wilayah_per_edisi"]
        self.upah = metadata_histori.tables["keputusan_upah_historis"]
        with self.engine.begin() as c:
            c.execute(insert(self.sumber).values(
                id_sumber="UJI-SUMBER", jenis_sumber="kode_wilayah", penerbit="Instansi Uji",
                judul="Hanya sintetis", edisi="EDISI-UJI", url_resmi="https://example.org/placeholder",
                sha256_berkas_asli="a" * 64, izin_distribusi="belum_diperiksa",
                status_verifikasi="draf"
            ))
            for edisi in ["E1", "E2"]:
                c.execute(insert(self.wilayah).values(
                    sistem_kode="UJI", edisi=edisi, kode_wilayah="01",
                    nama_wilayah="Provinsi Contoh", jenis_wilayah="provinsi",
                    id_sumber="UJI-SUMBER", status_verifikasi="draf"
                ))
                c.execute(insert(self.wilayah).values(
                    sistem_kode="UJI", edisi=edisi, kode_wilayah="0101",
                    nama_wilayah="Kabupaten Contoh", jenis_wilayah="kabupaten",
                    kode_induk="01", id_sumber="UJI-SUMBER", status_verifikasi="draf"
                ))

    def tearDown(self):
        self.engine.dispose()

    def test_edisi_wilayah_bisa_berdampingan(self):
        with self.engine.connect() as c:
            hasil = c.execute(
                select(self.wilayah.c.edisi).where(self.wilayah.c.kode_wilayah == "0101")
            ).scalars().all()
        self.assertEqual(set(hasil), {"E1", "E2"})

    def test_induk_harus_ada_dalam_sistem_edisi_yang_sama(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as c:
                c.execute(insert(self.wilayah).values(
                    sistem_kode="UJI", edisi="E1", kode_wilayah="0199",
                    nama_wilayah="Daerah tanpa induk", jenis_wilayah="kabupaten",
                    kode_induk="99", id_sumber="UJI-SUMBER", status_verifikasi="draf"
                ))

    def test_revisi_keputusan_tersimpan(self):
        keputusan = dict(
            sistem_kode="UJI", edisi_wilayah="E1", kode_wilayah="01",
            tahun=2026, jenis_upah="UMP", nilai_rupiah=100000,
            tanggal_mulai=date(2026, 1, 1), tanggal_keputusan=date(2025, 12, 1),
            id_sumber="UJI-SUMBER", status_verifikasi="draf"
        )
        with self.engine.begin() as c:
            c.execute(insert(self.upah).values(
                **keputusan, id_keputusan="UJI-1", nomor_keputusan="CONTOH-01",
                status_keputusan="diganti"))
            c.execute(insert(self.upah).values(
                **keputusan, id_keputusan="UJI-2", nomor_keputusan="CONTOH-02",
                id_keputusan_digantikan="UJI-1", status_keputusan="berlaku"))
        with self.engine.connect() as c:
            self.assertEqual(c.execute(select(self.upah.c.id_keputusan)).rowcount, -1)
            self.assertEqual(len(c.execute(select(self.upah.c.id_keputusan)).all()), 2)

    def test_keputusan_tidak_boleh_merujuk_wilayah_tidak_ada(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as c:
                c.execute(insert(self.upah).values(
                    id_keputusan="UJI-X", sistem_kode="UJI", edisi_wilayah="E1",
                    kode_wilayah="999", tahun=2026, jenis_upah="UMK",
                    nilai_rupiah=100000, tanggal_mulai=date(2026, 1, 1),
                    nomor_keputusan="CONTOH-X", tanggal_keputusan=date(2025, 12, 1),
                    status_keputusan="berlaku", id_sumber="UJI-SUMBER",
                    status_verifikasi="draf"
                ))

    def test_nominal_nol_ditolak(self):
        with self.assertRaises(IntegrityError):
            with self.engine.begin() as c:
                c.execute(insert(self.upah).values(
                    id_keputusan="UJI-X", sistem_kode="UJI", edisi_wilayah="E1",
                    kode_wilayah="01", tahun=2026, jenis_upah="UMP",
                    nilai_rupiah=0, tanggal_mulai=date(2026, 1, 1),
                    nomor_keputusan="CONTOH-X", tanggal_keputusan=date(2025, 12, 1),
                    status_keputusan="berlaku", id_sumber="UJI-SUMBER",
                    status_verifikasi="draf"
                ))

    def test_idempoten_tabel(self):
        metadata_histori.create_all(self.engine, checkfirst=True)
        self.assertEqual(set(inspect(self.engine).get_table_names()), set(metadata_histori.tables))

    def test_ddl_portabel(self):
        dialects = [
            postgresql.dialect(), mysql.dialect(), mssql.dialect(),
            oracle.dialect(), sqlite.dialect(),
        ]
        for dialect in dialects:
            for table in metadata_histori.sorted_tables:
                with self.subTest(dialect=dialect.name, table=table.name):
                    self.assertIn("CREATE TABLE", str(CreateTable(table).compile(dialect=dialect)))

if __name__ == "__main__":
    unittest.main()
