"""Impor taksonomi KBJI kandidat ke tabel versi; hanya status 'ditinjau'.

Tidak memverifikasi keaslian dokumen pemerintah atau mengesahkan hak lisensi.
Jalankan hanya setelah pemeriksaan manusia atas paket sumber.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from sqlalchemy import inspect, insert, select

from nor_id.basis_data import buat_mesin
from nor_id.skema_histori import sumber, taksonomi_kbji
from scripts.audit_kbji import audit_taksonomi
from scripts.validasi_manifest_sumber import validasi_manifest


def siapkan_paket(csv_path: Path, manifest_path: Path, sumber_asli: Path,
                  persetujuan_path: Path) -> tuple[list[dict], dict, dict]:
    """Validasi fail-closed. 'Persetujuan' adalah pernyataan manusia, bukan verifikasi mesin."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    masalah = validasi_manifest(manifest)
    if masalah:
        raise ValueError("Manifest tidak sah: " + "; ".join(masalah))
    if manifest["jenis_sumber"] != "klasifikasi_kbji":
        raise ValueError("Manifest bukan klasifikasi KBJI")
    if manifest["izin_distribusi"] != "diizinkan" or not manifest["rujukan_izin"]:
        raise ValueError("Hak redistribusi wajib diperiksa dan memiliki bukti")
    if manifest["status"] != "menunggu_verifikasi":
        raise ValueError("Tahap ini hanya menerima manifest menunggu_verifikasi")
    digest_asli = hashlib.sha256(sumber_asli.read_bytes()).hexdigest()
    if not manifest["sha256_berkas_sumber"] or digest_asli != manifest["sha256_berkas_sumber"].lower():
        raise ValueError("SHA-256 dokumen sumber tidak cocok dengan manifest")
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        required = {"edisi", "kode", "nama", "kode_induk", "tingkat"}
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != required:
            raise ValueError("CSV wajib memiliki tepat edisi,kode,nama,kode_induk,tingkat")
        rows = list(reader)
    if not rows or any(None in row or any(value is None for value in row.values()) for row in rows):
        raise ValueError("CSV kosong atau baris CSV tidak sah")
    laporan = audit_taksonomi(rows, manifest["edisi"])
    if laporan["galat"]:
        raise ValueError("Taksonomi tidak sah: " + "; ".join(laporan["galat"]))
    digest_csv = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    persetujuan = json.loads(persetujuan_path.read_text(encoding="utf-8"))
    if not isinstance(persetujuan, dict):
        raise ValueError("Persetujuan harus objek JSON")
    if persetujuan.get("sha256_csv_diolah") != digest_csv or persetujuan.get("sha256_berkas_sumber") != digest_asli:
        raise ValueError("Persetujuan tidak cocok dengan berkas CSV/sumber")
    if persetujuan.get("edisi") != manifest["edisi"]:
        raise ValueError("Edisi persetujuan tidak cocok")
    if persetujuan.get("status") != "disetujui_untuk_impor_ditinjau":
        raise ValueError("Persetujuan impor belum diberikan")
    reviewer = persetujuan.get("peninjau")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Identitas peninjau manusia wajib diisi")
    try:
        d = date.fromisoformat(persetujuan["tanggal_persetujuan"])
        if d.isoformat() != persetujuan["tanggal_persetujuan"]:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise ValueError("Tanggal persetujuan harus tanggal ISO yang sah") from None
    id_sumber = "KANDIDAT-KBJI-" + digest_asli[:16]
    return rows, manifest, {"sha256_csv": digest_csv, "sha256_asli": digest_asli,
                            "id_sumber": id_sumber, "peninjau": reviewer.strip(),
                            "tanggal_persetujuan": d.isoformat()}


def terapkan_paket(url: str, rows: list[dict], manifest: dict, bukti: dict) -> dict:
    """Impor atomik idempoten ke DB migrasi head; menolak perubahan diam-diam."""
    engine = buat_mesin(url)
    try:
        with engine.begin() as con:
            tabel = set(inspect(con).get_table_names())
            if not {sumber.name, taksonomi_kbji.name}.issubset(tabel):
                raise RuntimeError("Skema KBJI belum dimigrasi. Jalankan alembic upgrade head pada DB yang sesuai.")
            source_values = dict(
                id_sumber=bukti["id_sumber"], jenis_sumber="klasifikasi_kbji",
                penerbit=manifest["penerbit"].strip(), judul=manifest["judul"].strip(),
                edisi=manifest["edisi"], url_resmi=manifest["url_resmi"],
                sha256_berkas_asli=bukti["sha256_asli"], izin_distribusi="diizinkan",
                rujukan_izin=manifest["rujukan_izin"], status_verifikasi="ditinjau",
                peninjau=bukti["peninjau"],
                tanggal_verifikasi=date.fromisoformat(bukti["tanggal_persetujuan"]),
            )
            prior = con.execute(select(sumber).where(sumber.c.id_sumber == bukti["id_sumber"])).mappings().first()
            if prior is None:
                con.execute(insert(sumber).values(source_values))
            elif any(prior[k] != v for k, v in source_values.items()):
                raise ValueError("Sumber dengan ID sama memiliki isi berbeda; penimpaan dilarang")
            dibuat = 0
            for row in sorted(rows, key=lambda r: (int(r["tingkat"]), r["kode"])):
                nilai = dict(edisi=row["edisi"], kode=row["kode"], nama=row["nama"],
                             kode_induk=row["kode_induk"] or None, tingkat=int(row["tingkat"]),
                             id_sumber=bukti["id_sumber"], status_verifikasi="ditinjau")
                old = con.execute(select(taksonomi_kbji).where(
                    (taksonomi_kbji.c.edisi == nilai["edisi"]) & (taksonomi_kbji.c.kode == nilai["kode"])
                )).mappings().first()
                if old is not None:
                    if any(old[k] != v for k, v in nilai.items()):
                        raise ValueError("Kode sudah ada dengan isi berbeda; revisi wajib melalui proses terpisah")
                    continue
                con.execute(insert(taksonomi_kbji).values(nilai))
                dibuat += 1
        return {"id_sumber": bukti["id_sumber"], "jumlah_baris": len(rows),
                "baris_baru": dibuat, "status": "ditinjau_bukan_terverifikasi"}
    finally:
        engine.dispose()
