"""Impor kandidat keputusan UMP/UMK historis (ditinjau), bukan publikasi resmi."""
from __future__ import annotations
import csv
import hashlib
import json
from datetime import date
from pathlib import Path

from sqlalchemy import inspect, insert, select, event

from nor_id.basis_data import buat_mesin
from nor_id.skema_histori import sumber, wilayah, keputusan
from scripts.audit_upah_minimum import audit_upah, KOLOM as KOLOM_UPAH
from scripts.audit_wilayah import KOLOM as KOLOM_WILAYAH
from scripts.audit_paket_nasional import audit_rantai_keputusan
from scripts.validasi_manifest_sumber import validasi_manifest


def baca_csv(path: Path, fields: set[str]):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)) or set(reader.fieldnames) != fields:
            raise ValueError(f"CSV {path.name} tidak cocok dengan kolom wajib")
        rows = list(reader)
    if not rows or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError(f"CSV {path.name} kosong atau baris tidak lengkap")
    return rows


def id_keputusan(r: dict, nomor: str):
    k = "|".join((r["sistem_kode"], r["edisi_wilayah"], r["kode_wilayah"],
                  r["tahun"], r["jenis_upah"], nomor))
    return "KAND-UPAH-" + hashlib.sha256(k.encode("utf-8")).hexdigest()[:32]


def siapkan_paket(csv_upah: Path, csv_wilayah: Path, manifest_path: Path,
                  sumber_asli: Path, persetujuan_path: Path):
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = validasi_manifest(m)
    if errors:
        raise ValueError("Manifest tidak sah: " + "; ".join(errors))
    if m["jenis_sumber"] != "upah_minimum" or m["status"] != "menunggu_verifikasi":
        raise ValueError("Hanya menerima manifest calon upah_minimum menunggu_verifikasi")
    if m["izin_distribusi"] != "diizinkan" or not m["rujukan_izin"]:
        raise ValueError("Bukti hak redistribusi wajib diisi")
    sha_asli = hashlib.sha256(sumber_asli.read_bytes()).hexdigest()
    if sha_asli != m["sha256_berkas_sumber"]:
        raise ValueError("Checksum berkas sumber asli tidak cocok")
    rows = baca_csv(csv_upah, set(KOLOM_UPAH))
    regions = baca_csv(csv_wilayah, set(KOLOM_WILAYAH))
    keys = {(r["sistem_kode"], r["edisi_wilayah"], r["tahun"]) for r in rows}
    if len(keys) != 1:
        raise ValueError("Paket keputusan harus satu sistem kode, edisi wilayah, dan tahun")
    system, edition, year = next(iter(keys))
    if m["edisi"] != year:
        raise ValueError("Edisi manifest upah harus sama dengan tahun keputusan")
    audit = audit_upah(rows, regions)
    if audit["galat"]:
        raise ValueError("Audit UMP/UMK gagal: " + "; ".join(audit["galat"]))
    chain = audit_rantai_keputusan(rows)
    if chain:
        raise ValueError("Rantai keputusan gagal: " + "; ".join(chain))
    sha_csv = hashlib.sha256(csv_upah.read_bytes()).hexdigest()
    sha_regions = hashlib.sha256(csv_wilayah.read_bytes()).hexdigest()
    approval = json.loads(persetujuan_path.read_text(encoding="utf-8"))
    if not isinstance(approval, dict):
        raise ValueError("Persetujuan harus JSON object")
    if any((approval.get(k) != v for k, v in {
        "sha256_csv_diolah": sha_csv, "sha256_csv_wilayah": sha_regions,
        "sha256_berkas_sumber": sha_asli, "sistem_kode": system,
        "edisi_wilayah": edition, "tahun": year,
        "status": "disetujui_untuk_impor_ditinjau",
    }.items())):
        raise ValueError("Checksum atau identitas keputusan tidak cocok dengan persetujuan")
    reviewer = approval.get("peninjau")
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Peninjau manusia wajib dicatat")
    try:
        approval_date = date.fromisoformat(approval["tanggal_persetujuan"])
        if approval_date.isoformat() != approval["tanggal_persetujuan"]:
            raise ValueError()
    except (TypeError, ValueError, KeyError):
        raise ValueError("Tanggal persetujuan tidak sah") from None
    return rows, regions, m, {
        "id_sumber": "KANDIDAT-UPAH-" + sha_asli[:16], "sha_asli": sha_asli,
        "peninjau": reviewer.strip(), "tanggal_persetujuan": approval_date.isoformat(),
    }


def urutan_keputusan(rows):
    """Urutkan keputusan sebelumnya sebelum pengganti, setelah audit bebas siklus."""
    by_key = {id_keputusan(r, r["nomor_keputusan"]): r for r in rows}
    pending = dict(by_key)
    output = []
    while pending:
        ready = [(k, r) for k, r in pending.items() if not r["nomor_keputusan_digantikan"]
                 or id_keputusan(r, r["nomor_keputusan_digantikan"]) not in pending]
        if not ready:
            raise ValueError("Rantai keputusan siklik/tidak sah")
        for key, row in sorted(ready):
            output.append(row)
            del pending[key]
    return output


def terapkan_paket(url: str, rows, regions, m, proof):
    engine = buat_mesin(url)
    if engine.dialect.name == "sqlite":
        @event.listens_for(engine, "connect")
        def _fk(conn, _):
            conn.execute("PRAGMA foreign_keys=ON")
    try:
        with engine.begin() as db:
            if not {sumber.name, wilayah.name, keputusan.name}.issubset(inspect(db).get_table_names()):
                raise RuntimeError("Migrasi skema historis wilayah/upah belum dijalankan")
            codes = {(r["sistem_kode"], r["edisi_wilayah"], r["kode_wilayah"]) for r in rows}
            wilayah_db = {}
            for sys, edition, code in codes:
                old = db.execute(select(wilayah).where(
                    (wilayah.c.sistem_kode == sys) & (wilayah.c.edisi == edition) &
                    (wilayah.c.kode_wilayah == code)
                )).mappings().first()
                if old is None or old["status_verifikasi"] not in ("ditinjau", "terverifikasi"):
                    raise ValueError(f"Wilayah {sys}/{edition}/{code} harus tersedia dan ditinjau di DB")
                wilayah_db[(sys, edition, code)] = old
            for r in rows:
                w = wilayah_db[(r["sistem_kode"], r["edisi_wilayah"], r["kode_wilayah"])]
                if (r["jenis_upah"] == "UMP" and w["jenis_wilayah"] != "provinsi") or (
                    r["jenis_upah"] == "UMK" and w["jenis_wilayah"] not in ("kabupaten", "kota")):
                    raise ValueError("Jenis wilayah DB tidak sesuai UMP/UMK")
            # Tolak keputusan aktif ganda lintas paket; revisi membutuhkan alur terpisah.
            for r in rows:
                if r["status_keputusan"] != "berlaku":
                    continue
                target_id = id_keputusan(r, r["nomor_keputusan"])
                active = db.execute(select(keputusan.c.id_keputusan).where(
                    (keputusan.c.sistem_kode == r["sistem_kode"]) &
                    (keputusan.c.edisi_wilayah == r["edisi_wilayah"]) &
                    (keputusan.c.kode_wilayah == r["kode_wilayah"]) &
                    (keputusan.c.tahun == int(r["tahun"])) &
                    (keputusan.c.jenis_upah == r["jenis_upah"]) &
                    (keputusan.c.status_keputusan == "berlaku")
                )).scalars().all()
                if any(existing != target_id for existing in active):
                    raise ValueError("Keputusan berstatus berlaku berbeda sudah ada di DB untuk wilayah/tahun/jenis")
            record_source = dict(
                id_sumber=proof["id_sumber"], jenis_sumber="upah_minimum", penerbit=m["penerbit"].strip(),
                judul=m["judul"].strip(), edisi=m["edisi"], url_resmi=m["url_resmi"],
                sha256_berkas_asli=proof["sha_asli"], izin_distribusi="diizinkan",
                rujukan_izin=m["rujukan_izin"], status_verifikasi="ditinjau",
                peninjau=proof["peninjau"],
                tanggal_verifikasi=date.fromisoformat(proof["tanggal_persetujuan"]),
            )
            prev_source = db.execute(select(sumber).where(sumber.c.id_sumber == proof["id_sumber"])).mappings().first()
            if prev_source is None:
                db.execute(insert(sumber).values(record_source))
            elif any(prev_source[k] != v for k, v in record_source.items()):
                raise ValueError("Sumber upah sudah ada dan berbeda")
            added = 0
            for r in urutan_keputusan(rows):
                new = dict(
                    id_keputusan=id_keputusan(r, r["nomor_keputusan"]),
                    sistem_kode=r["sistem_kode"], edisi_wilayah=r["edisi_wilayah"],
                    kode_wilayah=r["kode_wilayah"], tahun=int(r["tahun"]),
                    jenis_upah=r["jenis_upah"], nilai_rupiah=int(r["nilai_rupiah"]),
                    tanggal_mulai=date.fromisoformat(r["tanggal_mulai"]),
                    nomor_keputusan=r["nomor_keputusan"],
                    tanggal_keputusan=date.fromisoformat(r["tanggal_keputusan"]),
                    status_keputusan=r["status_keputusan"],
                    id_keputusan_digantikan=(id_keputusan(r, r["nomor_keputusan_digantikan"])
                                              if r["nomor_keputusan_digantikan"] else None),
                    id_sumber=proof["id_sumber"], status_verifikasi="ditinjau",
                )
                prev = db.execute(select(keputusan).where(keputusan.c.id_keputusan == new["id_keputusan"])).mappings().first()
                if prev is not None:
                    if any(prev[k] != v for k, v in new.items()):
                        raise ValueError("Keputusan sudah ada tetapi isi berbeda: menimpa dilarang")
                else:
                    db.execute(insert(keputusan).values(new))
                    added += 1
        return {"jumlah_baris": len(rows), "baris_baru": added,
                "status": "ditinjau_bukan_terverifikasi", "id_sumber": proof["id_sumber"]}
    finally:
        engine.dispose()
