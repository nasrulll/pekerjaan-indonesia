"""Gerbang audit kandidat KBJI, wilayah dan UMP/UMK; tanpa publikasi data.

Menautkan manifest, checksum sumber primer (jika tersedia), edisi dan relasi
keputusan pengganti. Laporan lulus BUKAN persetujuan publikasi pemerintah.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def baca_tabel(path: Path, wajib: set[str]) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        kolom = reader.fieldnames or []
        if len(kolom) != len(set(kolom)) or not wajib.issubset(kolom):
            raise ValueError(f"{path.name}: kolom tidak lengkap atau duplikat; wajib {sorted(wajib)}")
        rows = list(reader)
        if any(None in row or any(value is None for value in row.values()) for row in rows):
            raise ValueError(f"{path.name}: baris dengan kolom berlebih atau kurang")
        return rows


def audit_rantai_keputusan(rows: list[dict[str, str]]) -> list[str]:
    """Referensi penggantian harus satu wilayah/edisi/tahun/jenis dan bebas siklus."""
    kunci = ("sistem_kode", "edisi_wilayah", "kode_wilayah", "tahun", "jenis_upah")
    kelompok: dict[tuple[str, ...], dict[str, dict[str, str]]] = defaultdict(dict)
    masalah: list[str] = []
    for no, row in enumerate(rows, 2):
        grup = tuple(row.get(k, "").strip() for k in kunci)
        nomor = row.get("nomor_keputusan", "").strip()
        if nomor in kelompok[grup]:
            masalah.append(f"baris {no}: nomor keputusan duplikat dalam wilayah/tahun/jenis")
        kelompok[grup][nomor] = row
    for grup, indeks in kelompok.items():
        penerus: dict[str, list[str]] = defaultdict(list)
        for nomor, row in indeks.items():
            lama = row.get("nomor_keputusan_digantikan", "").strip()
            if not lama:
                continue
            if lama == nomor:
                masalah.append(f"{nomor}: tidak dapat menggantikan diri sendiri")
            elif lama not in indeks:
                masalah.append(f"{nomor}: keputusan lama {lama} tidak ada pada wilayah/edisi/tahun/jenis yang sama")
            else:
                penerus[lama].append(nomor)
                if indeks[lama].get("status_keputusan") != "diganti":
                    masalah.append(f"{nomor}: keputusan yang digantikan {lama} harus berstatus diganti")
        for lama, baru in penerus.items():
            if len(baru) != 1:
                masalah.append(f"{lama}: digantikan oleh lebih dari satu keputusan")
        for nomor, row in indeks.items():
            if row.get("status_keputusan") == "diganti" and nomor not in penerus:
                masalah.append(f"{nomor}: berstatus diganti tetapi keputusan pengganti tidak ditemukan")
            ditelusuri: set[str] = set()
            sekarang = nomor
            while sekarang in indeks:
                if sekarang in ditelusuri:
                    masalah.append(f"{nomor}: siklus dalam rantai keputusan")
                    break
                ditelusuri.add(sekarang)
                sekarang = indeks[sekarang].get("nomor_keputusan_digantikan", "").strip()
                if not sekarang:
                    break
    return sorted(set(masalah))


def audit_paket(berkas: dict[str, tuple[Path, Path, Path | None]],
                pekerjaan: Path | None = None) -> dict:
    """Audit semua input secara read-only; tidak pernah menulis CSV master."""
    from scripts.audit_kbji import audit_taksonomi, kandidat_cocok, KOLOM as KBJI_KOLOM
    from scripts.audit_wilayah import audit_wilayah, KOLOM as WILAYAH_KOLOM
    from scripts.audit_upah_minimum import audit_upah, KOLOM as UPAH_KOLOM
    from scripts.validasi_manifest_sumber import validasi_manifest

    jenis_sumber = {"kbji": "klasifikasi_kbji", "wilayah": "kode_wilayah", "upah": "upah_minimum"}
    kolom = {"kbji": set(KBJI_KOLOM), "wilayah": WILAYAH_KOLOM, "upah": UPAH_KOLOM}
    galat, peringatan, data, ringkasan = [], [], {}, {}
    for jenis in ("kbji", "wilayah", "upah"):
        if jenis not in berkas:
            continue
        csv_path, manifest_path, asli_path = berkas[jenis]
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        galat.extend(f"{jenis}: {e}" for e in validasi_manifest(manifest))
        if not isinstance(manifest, dict):
            continue
        if manifest.get("jenis_sumber") != jenis_sumber[jenis]:
            galat.append(f"{jenis}: jenis_sumber harus {jenis_sumber[jenis]}")
        rows = baca_tabel(csv_path, kolom[jenis])
        data[jenis] = (rows, manifest)
        sha_csv = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        ringkasan[jenis] = {"jumlah_baris": len(rows), "sha256_csv_olahan": sha_csv,
                           "bukti_primer_diperiksa": False}
        if asli_path is None:
            peringatan.append(f"{jenis}: berkas primer belum diberikan; checksum sumber belum diverifikasi")
        elif not manifest.get("sha256_berkas_sumber"):
            galat.append(f"{jenis}: manifest tidak memiliki sha256_berkas_sumber")
        elif not isinstance(manifest["sha256_berkas_sumber"], str) or hashlib.sha256(asli_path.read_bytes()).hexdigest().lower() != manifest["sha256_berkas_sumber"].lower():
            galat.append(f"{jenis}: checksum berkas primer tidak sesuai manifest")
        else:
            ringkasan[jenis]["bukti_primer_diperiksa"] = True
        if manifest.get("status") == "terverifikasi":
            # Pernyataan sendiri di manifest tidak pernah memberikan otorisasi publikasi.
            peringatan.append(f"{jenis}: status manifest tidak menggantikan tinjauan manusia")

    if "kbji" in data:
        rows, manifest = data["kbji"]
        laporan = audit_taksonomi(rows, manifest.get("edisi", ""))
        galat.extend("kbji: " + e for e in laporan["galat"])
        ringkasan["kbji"]["jumlah_kode_unik"] = laporan["jumlah_kode_unik"]
        if pekerjaan is not None:
            p = baca_tabel(pekerjaan, {"occupation_id", "preferred_name_id"})
            ringkasan["kbji"]["jumlah_kandidat_teks"] = len(kandidat_cocok(p, rows))

    if "wilayah" in data:
        rows, manifest = data["wilayah"]
        galat.extend("wilayah: " + e for e in audit_wilayah(rows)["galat"])
        if any(r.get("edisi") != manifest.get("edisi") for r in rows):
            galat.append("wilayah: edisi CSV tidak sesuai manifest")
    if "upah" in data:
        if "wilayah" not in data:
            galat.append("upah: audit memerlukan dataset wilayah dalam paket yang sama")
        else:
            rows, manifest = data["upah"]
            wilayah, _ = data["wilayah"]
            galat.extend("upah: " + e for e in audit_upah(rows, wilayah)["galat"])
            galat.extend("upah: " + e for e in audit_rantai_keputusan(rows))
            if not manifest.get("edisi_wilayah") or any(
                r.get("edisi_wilayah") != manifest["edisi_wilayah"] for r in rows
            ):
                galat.append("upah: edisi_wilayah manifest wajib dan harus cocok dengan CSV")

    return {"jumlah_dataset": len(berkas), "dataset": ringkasan,
            "galat": sorted(set(galat)), "peringatan": sorted(set(peringatan)),
            "layak_diajukan_untuk_tinjauan": not galat,
            "status_publikasi": "DIBLOKIR_MENUNGGU_PERSETUJUAN_MANUSIA"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit lintas-dataset RPI; tidak memublikasikan data resmi")
    for jenis in ("kbji", "wilayah", "upah"):
        parser.add_argument("--" + jenis, type=Path)
        parser.add_argument("--manifest-" + jenis, type=Path)
        parser.add_argument("--berkas-asli-" + jenis, type=Path)
    parser.add_argument("--pekerjaan", type=Path)
    parser.add_argument("--laporan", type=Path)
    args = parser.parse_args()
    paket = {}
    for jenis in ("kbji", "wilayah", "upah"):
        csv_path, manifest_path = getattr(args, jenis), getattr(args, "manifest_" + jenis)
        if getattr(args, "berkas_asli_" + jenis) and not csv_path:
            parser.error(f"--berkas-asli-{jenis} memerlukan --{jenis}")
        if bool(csv_path) != bool(manifest_path):
            parser.error(f"--{jenis} harus disertai --manifest-{jenis}")
        if csv_path:
            paket[jenis] = csv_path, manifest_path, getattr(args, "berkas_asli_" + jenis)
    if not paket:
        parser.error("Minimal satu dataset dan manifest diperlukan")
    try:
        hasil = audit_paket(paket, args.pekerjaan)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError, csv.Error) as exc:
        parser.error(f"Input gagal diperiksa: {exc}")
    teks = json.dumps(hasil, ensure_ascii=False, indent=2) + "\n"
    print(teks, end="")
    if args.laporan:
        args.laporan.write_text(teks, encoding="utf-8")
    return int(bool(hasil["galat"]))


if __name__ == "__main__":
    raise SystemExit(main())
