"""Impor kandidat wilayah administratif secara transaksional; tidak mengesahkan data resmi."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from sqlalchemy import inspect, insert, select, event
from nor_id.basis_data import buat_mesin
from nor_id.skema_histori import sumber, wilayah
from scripts.audit_wilayah import audit_wilayah
from scripts.validasi_manifest_sumber import validasi_manifest

KOLOM = {"sistem_kode", "edisi", "kode_wilayah", "nama_wilayah", "jenis_wilayah", "kode_induk"}


def siapkan_paket(csv_path: Path, manifest_path: Path, sumber_asli: Path,
                  persetujuan_path: Path) -> tuple[list[dict], dict, dict]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    masalah = validasi_manifest(manifest)
    if masalah:
        raise ValueError("Manifest tidak sah: " + "; ".join(masalah))
    if manifest["jenis_sumber"] != "kode_wilayah" or manifest["status"] != "menunggu_verifikasi":
        raise ValueError("Hanya menerima manifest calon kode_wilayah menunggu_verifikasi")
    if manifest["izin_distribusi"] != "diizinkan" or not manifest["rujukan_izin"]:
        raise ValueError("Bukti hak redistribusi wajib diisi dan ditinjau")
    checksum_asli = hashlib.sha256(sumber_asli.read_bytes()).hexdigest()
    if manifest["sha256_berkas_sumber"] != checksum_asli:
        raise ValueError("Checksum SHA-256 berkas asli tidak cocok")
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or set(reader.fieldnames) != KOLOM or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError("Kolom CSV wilayah tidak sesuai kontrak")
        rows = list(reader)
    if not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError("CSV kosong atau jumlah kolom baris tidak sah")
    if any(r["edisi"] != manifest["edisi"] for r in rows):
        raise ValueError("Edisi kode wilayah tidak sesuai manifest")
    laporan = audit_wilayah(rows)
    if laporan["galat"]:
        raise ValueError("Audit wilayah gagal: " + "; ".join(laporan["galat"]))
    sistem_kode = {r["sistem_kode"] for r in rows}
    if len(sistem_kode) != 1:
        raise ValueError("Satu paket harus menggunakan satu sistem kode wilayah")
    checksum_csv = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    approval = json.loads(persetujuan_path.read_text(encoding="utf-8"))
    if not isinstance(approval, dict):
        raise ValueError("Persetujuan harus objek JSON")
    if (approval.get("sha256_csv_diolah") != checksum_csv
            or approval.get("sha256_berkas_sumber") != checksum_asli
            or approval.get("edisi") != manifest["edisi"]
            or approval.get("sistem_kode") != next(iter(sistem_kode))):
        raise ValueError("Berkas atau edisi/sistem kode tidak cocok dengan persetujuan")
    if approval.get("status") != "disetujui_untuk_impor_ditinjau":
        raise ValueError("Persetujuan impor ditinjau belum diberikan")
    peninjau = approval.get("peninjau")
    if not isinstance(peninjau, str) or not peninjau.strip():
        raise ValueError("Identitas peninjau wajib diisi")
    try:
        tanggal = date.fromisoformat(approval["tanggal_persetujuan"])
        if tanggal.isoformat() != approval["tanggal_persetujuan"]:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise ValueError("Tanggal persetujuan tidak sah") from None
    return rows, manifest, {"id_sumber": "KANDIDAT-WIL-" + checksum_asli[:16],
                            "checksum_csv": checksum_csv, "checksum_asli": checksum_asli,
                            "peninjau": peninjau.strip(), "tanggal_persetujuan": tanggal.isoformat()}


def terapkan_paket(url: str, rows: list[dict], manifest: dict, bukti: dict) -> dict:
    engine = buat_mesin(url)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _sqlite_fk(conn, _):
            conn.execute("PRAGMA foreign_keys=ON")
    try:
        with engine.begin() as con:
            if not {sumber.name, wilayah.name}.issubset(inspect(con).get_table_names()):
                raise RuntimeError("Database belum memiliki tabel historis; jalankan migrasi Alembic terlebih dahulu")
            data_sumber = dict(
                id_sumber=bukti["id_sumber"], jenis_sumber="kode_wilayah",
                penerbit=manifest["penerbit"].strip(), judul=manifest["judul"].strip(),
                edisi=manifest["edisi"], url_resmi=manifest["url_resmi"],
                sha256_berkas_asli=bukti["checksum_asli"], izin_distribusi="diizinkan",
                rujukan_izin=manifest["rujukan_izin"], status_verifikasi="ditinjau",
                peninjau=bukti["peninjau"],
                tanggal_verifikasi=date.fromisoformat(bukti["tanggal_persetujuan"]),
            )
            old_source = con.execute(select(sumber).where(sumber.c.id_sumber == data_sumber["id_sumber"])).mappings().first()
            if old_source is None:
                con.execute(insert(sumber).values(data_sumber))
            elif any(old_source[k] != v for k, v in data_sumber.items()):
                raise ValueError("Sumber yang sudah ada berbeda; tidak boleh ditimpa")
            dibuat = 0
            for row in sorted(rows, key=lambda r: (r["jenis_wilayah"] != "provinsi", r["kode_wilayah"])):
                data = dict(sistem_kode=row["sistem_kode"], edisi=row["edisi"],
                            kode_wilayah=row["kode_wilayah"], nama_wilayah=row["nama_wilayah"],
                            jenis_wilayah=row["jenis_wilayah"], kode_induk=row["kode_induk"] or None,
                            id_sumber=bukti["id_sumber"], status_verifikasi="ditinjau")
                old = con.execute(select(wilayah).where(
                    (wilayah.c.sistem_kode == data["sistem_kode"]) &
                    (wilayah.c.edisi == data["edisi"]) &
                    (wilayah.c.kode_wilayah == data["kode_wilayah"])
                )).mappings().first()
                if old is not None:
                    if any(old[k] != v for k, v in data.items()):
                        raise ValueError("Wilayah dengan identitas sama berbeda; diperlukan revisi eksplisit")
                    continue
                con.execute(insert(wilayah).values(data))
                dibuat += 1
        return {"jumlah_baris": len(rows), "baris_baru": dibuat, "id_sumber": bukti["id_sumber"],
                "status": "ditinjau_bukan_terverifikasi"}
    finally:
        engine.dispose()
