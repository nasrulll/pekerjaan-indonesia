#!/usr/bin/env python3
"""Safely upsert the checked Git/CSV catalog into an initialized PostgreSQL DB.

Requires optional psycopg v3. Changes are transactional and are made only with
--apply; deletions are intentionally never implicit.
"""
from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from validate import ROOT, check, read_csv

from catalog_tables import COLUMNS

TABLES = (
    ("data_sources", "sources.csv", "source_id"),
    ("sectors", "reference/sectors.csv", "sector_id"),
    ("occupations", "occupations.csv", "occupation_id"),
    ("employment_contexts", "reference/employment_contexts.csv", "context_code"),
    ("job_titles", "job_titles.csv", "title_id"),
    ("kbji_mappings", "kbji_mappings.csv", "occupation_id,kbji_edition,kbji_code"),
    ("jabatan_nasional","jabatan_nasional.csv","id_jabatan"),
    ("wilayah_administratif","wilayah_administratif.csv","sistem_kode,kode_wilayah"),
    ("pemetaan_jabatan_kbji","pemetaan_jabatan_kbji.csv","id_jabatan,edisi_kbji,kode_kbji"),
    ("kompetensi_jabatan","kompetensi_jabatan.csv","id_kompetensi"),
    ("upah_minimum","upah_minimum.csv","id_upah"),
    ("statistik_upah","statistik_upah.csv","id_statistik"),
    ("kelas_gaji","kelas_gaji.csv","id_kelas_gaji"),
)


def rows_for(table: str, location: Path) -> list[dict]:
    rows = read_csv(location)
    for record in rows:
        if table == "occupations":
            record["last_reviewed"] = date.fromisoformat(record["last_reviewed"]) if record["last_reviewed"] else None
        if table == "kbji_mappings":
            record["verified_at"] = date.fromisoformat(record["verified_at"])
        if table in ('jabatan_nasional','wilayah_administratif','upah_minimum',
                     'statistik_upah','kelas_gaji','pemetaan_jabatan_kbji','kompetensi_jabatan'):
            # Typed PostgreSQL date/int columns with nullable CSV fields.
            for k in ('tanggal_verifikasi','tanggal_mulai'):
                if k in record and record[k]:
                    record[k] = date.fromisoformat(record[k])
            for k in ('tahun','nilai_rupiah','jumlah_sampel','nilai_dasar_rupiah'):
                if k in record and record[k]:
                    record[k] = int(record[k])
            for k,v in record.items():
                if v == '': record[k] = None
    return rows


def statements(table: str, rows: list[dict], keys: str) -> tuple[str, list[tuple]]:
    """Identifiers are defined by TABLES, never derived from user-supplied input."""
    if not rows:
        return "", []
    cols = COLUMNS[table]
    if set(rows[0]) != set(cols):
        raise ValueError(f"Unexpected CSV columns for {table}: {set(rows[0]) ^ set(cols)}")
    columns = ", ".join(cols)
    values = ", ".join("%s" for _ in cols)
    protected = set(keys.split(","))
    updates = ", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in protected)
    if table == "occupations":
        updates += ", updated_at = NOW()"
    clause = f"DO UPDATE SET {updates}" if updates else "DO NOTHING"
    sql = f"INSERT INTO {table} ({columns}) VALUES ({values}) ON CONFLICT ({keys}) {clause}"
    return sql, [tuple(row[col] for col in cols) for row in rows]


def load(dsn: str, root: Path = ROOT) -> dict[str, int]:
    try:
        import psycopg
    except ImportError as exc:
        raise RuntimeError("Instal dependensi: pip install -e '.[postgres]'") from exc
    if not dsn:
        raise ValueError("NOR_DATABASE_URL diperlukan untuk memuat PostgreSQL")
    if dsn.startswith("postgresql+psycopg://"):
        dsn = "postgresql://" + dsn[len("postgresql+psycopg://"):]
    if not (dsn.startswith("postgresql://") or dsn.startswith("postgres://")):
        raise ValueError("Hanya DSN PostgreSQL yang diterima")
    counts = {}
    with psycopg.connect(dsn) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT to_regclass('public.occupations')")
                if not cur.fetchone()[0]:
                    raise RuntimeError("Skema belum dibuat. Jalankan psql -f schema/postgresql.sql dahulu.")
                cur.execute("SELECT to_regclass('public.jabatan_nasional')")
                if not cur.fetchone()[0]:
                    raise RuntimeError("Migrasi v0.3 belum terpasang. Jalankan schema/postgresql_tambahan.sql untuk database lama.")
                for table, filename, keys in TABLES:
                    rows = rows_for(table, root / "data" / filename)
                    query, values = statements(table, rows, keys)
                    if values:
                        cur.executemany(query, values)
                    counts[table] = len(rows)
                # Normalized aliases for consumers who prefer relational joins.
                names = []
                for occ in read_csv(root / "data" / "occupations.csv"):
                    names.extend((occ["occupation_id"], alias.strip())
                                 for alias in occ["alternative_names"].split("|") if alias.strip())
                if names:
                    cur.executemany("""
                        INSERT INTO occupation_aliases (occupation_id, alternative_name_id)
                        VALUES (%s, %s) ON CONFLICT (occupation_id, alternative_name_id) DO NOTHING
                    """, names)
                counts["occupation_aliases"] = len(names)
    return counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Tulis perubahan ke database")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors, stats = check(args.root)
    if errors:
        parser.error("Dataset tidak valid:\n" + "\n".join(errors))
    print("Dataset valid:", stats)
    if not args.apply:
        print("Dry run: tidak ada koneksi atau perubahan. Gunakan --apply untuk upsert PostgreSQL.")
        return
    dsn = os.getenv("RPI_DATABASE_URL") or os.getenv("NOR_DATABASE_URL", "")
    print("Committed PostgreSQL upserts:", load(dsn, args.root))
    print("Catatan: penghapusan rekord lama tidak dilakukan otomatis. Audit perubahan untuk data usang.")


if __name__ == "__main__":
    main()
