"""CLI audit/impor UMP dan UMK kandidat, selalu status ditinjau."""
import argparse
import json
import os
from pathlib import Path
from nor_id.impor_upah_ditinjau import siapkan_paket, terapkan_paket


def main():
    p = argparse.ArgumentParser(description="Impor keputusan UMP/UMK historis kandidat")
    for field in ("csv-upah", "csv-wilayah", "manifest", "berkas-asli", "persetujuan"):
        p.add_argument("--" + field, type=Path, required=True)
    p.add_argument("--terapkan", action="store_true")
    args = p.parse_args()
    try:
        data = siapkan_paket(args.csv_upah, args.csv_wilayah, args.manifest,
                             args.berkas_asli, args.persetujuan)
        out = {"jumlah_baris": len(data[0]), "status": "siap_impor_ditinjau", "diterapkan": False}
        if args.terapkan:
            url = os.environ.get("RPI_DATABASE_URL")
            if not url:
                raise ValueError("RPI_DATABASE_URL belum disetel")
            out.update(terapkan_paket(url, *data))
            out["diterapkan"] = True
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as e:
        p.error(str(e))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
