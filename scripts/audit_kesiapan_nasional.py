"""CLI baca-saja: laporan integritas data terverifikasi di database historis."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from nor_id.basis_data import buat_mesin
from nor_id.kesiapan_publikasi import audit_kesiapan


def main():
    p = argparse.ArgumentParser(description="Audit integritas data resmi tanpa mengesahkan publikasi")
    p.add_argument("--database-url", default=os.getenv("RPI_DATABASE_URL"))
    p.add_argument("--laporan", type=Path)
    p.add_argument("--wajib-entri-terverifikasi", action="store_true",
                   help="Gagalkan gate rilis jika belum ada entri terverifikasi")
    args = p.parse_args()
    if not args.database_url:
        p.error("--database-url atau RPI_DATABASE_URL wajib diisi")
    try:
        engine = buat_mesin(args.database_url)
        try:
            report = audit_kesiapan(engine)
        finally:
            engine.dispose()
    except (OSError, ValueError, RuntimeError) as exc:
        p.error(str(exc))
    result = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(result, end="")
    if args.laporan:
        args.laporan.parent.mkdir(parents=True, exist_ok=True)
        args.laporan.write_text(result, encoding="utf-8")
    if report["temuan"]:
        return 1
    if args.wajib_entri_terverifikasi and report["status_kesiapan"] == "menunggu_dataset_resmi":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
