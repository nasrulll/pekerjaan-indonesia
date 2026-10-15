"""Audit taksonomi kandidat KBJI: tidak pernah mempublikasikan pemetaan resmi."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

try:
    from scripts.validasi_manifest_sumber import validasi_manifest
except ModuleNotFoundError:  # pemanggilan langsung dari scripts/
    from validasi_manifest_sumber import validasi_manifest

KOLOM = ("edisi", "kode", "nama", "kode_induk", "tingkat")
KODE = re.compile(r"[0-9]{1,8}\Z")


def normalisasi_nama(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def baca_csv(path: Path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = reader.fieldnames or []
        if len(header) != len(set(header)) or not set(KOLOM).issubset(header):
            return [], ["Header CSV harus mencakup: " + ", ".join(KOLOM)]
        return list(reader), []


def audit_taksonomi(rows: list[dict[str, str]], edisi: str):
    errors = []
    indeks = {}
    tingkat = Counter()
    for line, row in enumerate(rows, 2):
        kode, nama, induk, level = ((row.get(k) or "") for k in ("kode", "nama", "kode_induk", "tingkat"))
        if row.get("edisi") != edisi:
            errors.append(f"baris {line}: edisi tidak cocok dengan manifest")
        if not KODE.fullmatch(kode):
            errors.append(f"baris {line}: kode bukan 1–8 digit; nol awal harus dipertahankan")
        if not nama.strip() or nama != nama.strip():
            errors.append(f"baris {line}: nama kosong atau ada spasi tepi")
        if kode in indeks:
            errors.append(f"baris {line}: kode duplikat {kode}")
        if not level.isdigit() or int(level) not in range(1, 10):
            errors.append(f"baris {line}: tingkat harus 1–9")
        if induk and not KODE.fullmatch(induk):
            errors.append(f"baris {line}: kode induk bukan digit")
        if induk == kode:
            errors.append(f"baris {line}: induk diri sendiri")
        if kode and kode not in indeks:
            indeks[kode] = row
        if level.isdigit():
            tingkat[level] += 1
    for kode, row in indeks.items():
        induk = row.get("kode_induk") or ""
        level = row.get("tingkat") or ""
        if not induk and level.isdigit() and int(level) != 1:
            errors.append(f"kode {kode}: tingkat akar harus 1")
        if induk and induk not in indeks:
            errors.append(f"kode {kode}: induk {induk} tidak ditemukan")
        if induk in indeks:
            level_induk = indeks[induk].get("tingkat") or ""
            if level.isdigit() and level_induk.isdigit() and int(level) != int(level_induk) + 1:
                errors.append(f"kode {kode}: tingkat harus satu lebih dalam dari induk")
        seen, next_code = {kode}, induk
        while next_code and next_code in indeks:
            if next_code in seen:
                errors.append(f"kode {kode}: siklus hierarki")
                break
            seen.add(next_code)
            next_code = indeks[next_code].get("kode_induk") or ""
    return {
        "jumlah_baris": len(rows), "jumlah_kode_unik": len(indeks),
        "jumlah_per_tingkat": dict(sorted(tingkat.items())),
        "galat": sorted(set(errors))
    }


def kandidat_cocok(pekerjaan, taksonomi):
    """Kecocokan teks saja; kode tetap berstatus belum diverifikasi."""
    nama_kode = defaultdict(list)
    for item in taksonomi:
        nama_kode[normalisasi_nama(item["nama"])].append(item)
    result = []
    for item in pekerjaan:
        for match in nama_kode.get(normalisasi_nama(item["preferred_name_id"]), []):
            result.append({
                "occupation_id": item["occupation_id"], "nama_pekerjaan": item["preferred_name_id"],
                "edisi": match["edisi"], "kode_kandidat": match["kode"],
                "metode": "nama_persis_normalisasi", "status": "kandidat_belum_diverifikasi",
            })
    return result


def jalankan(csv_kbji: Path, manifest_json: Path, csv_pekerjaan: Path | None = None):
    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    errors = validasi_manifest(manifest)
    if not isinstance(manifest, dict):
        return {"galat": errors}, []
    if manifest.get("jenis_sumber") != "klasifikasi_kbji":
        errors.append("jenis_sumber harus klasifikasi_kbji")
    # Keaslian/izin sumber tidak dapat ditetapkan otomatis oleh alat ini.
    if manifest.get("status") == "terverifikasi":
        errors.append("Status terverifikasi membutuhkan review manual terpisah; alat audit tidak menerbitkannya")
    rows, csv_errors = baca_csv(csv_kbji)
    errors.extend(csv_errors)
    report = audit_taksonomi(rows, manifest.get("edisi") or "") if not csv_errors else {
        "jumlah_baris": 0, "jumlah_kode_unik": 0, "jumlah_per_tingkat": {}, "galat": []}
    errors.extend(report.pop("galat"))
    report.update({
        "edisi": manifest.get("edisi"), "status_keluaran": "audit_internal_belum_resmi",
        "checksum_csv_diolah": hashlib.sha256(csv_kbji.read_bytes()).hexdigest(),
        "galat": sorted(set(errors)),
    })
    candidates = []
    if csv_pekerjaan and not report["galat"]:
        with csv_pekerjaan.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"occupation_id", "preferred_name_id"}.issubset(reader.fieldnames or []):
                report["galat"].append("Berkas pekerjaan perlu occupation_id dan preferred_name_id")
            else:
                candidates = kandidat_cocok(list(reader), rows)
    report["jumlah_kandidat"] = len(candidates)
    return report, candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit KBJI internal, tidak menambah data resmi")
    parser.add_argument("--csv-kbji", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--csv-pekerjaan", type=Path)
    parser.add_argument("--laporan", type=Path)
    parser.add_argument("--kandidat", type=Path)
    args = parser.parse_args()
    try:
        report, candidates = jalankan(args.csv_kbji, args.manifest, args.csv_pekerjaan)
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        parser.error(f"Input tidak dapat diproses: {exc}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.laporan:
        args.laporan.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.kandidat and not report["galat"]:
        with args.kandidat.open("w", newline="", encoding="utf-8") as handle:
            columns = ("occupation_id", "nama_pekerjaan", "edisi", "kode_kandidat", "metode", "status")
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(candidates)
    return int(bool(report["galat"]))


if __name__ == "__main__":
    raise SystemExit(main())
