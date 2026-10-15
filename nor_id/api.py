"""Versioned, public read-only REST API for the curated occupation catalog.

CSV in Git is canonical. The database is a queryable snapshot, not a source of
truth. Draft records remain explicitly labeled draft; verified KBJI mappings
are returned only when present in the dataset.
"""
from __future__ import annotations

import csv
import io
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import bindparam, create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
NOTICE = "Katalog kurasi; tidak merupakan klasifikasi resmi KBJI. Periksa status dan bukti pemetaan."
VERSION = "0.3.0"


def database_url() -> str:
    custom = os.getenv("RPI_DATABASE_URL") or os.getenv("NOR_DATABASE_URL")
    if custom:
        return custom
    return "sqlite+pysqlite:///" + str(ROOT / "dist" / "pekerjaan-indonesia.sqlite3")


def engine_for(url: str) -> Engine:
    if url.startswith("sqlite"):
        # SQLite must have been built beforehand; don't silently open an empty DB.
        if url.startswith("sqlite+pysqlite:///"):
            file = Path(url[len("sqlite+pysqlite:///"):])
            if not file.is_file():
                raise RuntimeError(f"SQLite tidak ditemukan: {file}. Jalankan python scripts/build_sqlite.py")
        return create_engine(url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
    if not url.startswith("postgresql+psycopg://"):
        raise ValueError("NOR_DATABASE_URL harus sqlite+pysqlite:///... atau postgresql+psycopg://...")
    return create_engine(url, pool_pre_ping=True)


def db(request: Request) -> Engine:
    return request.app.state.engine


def escaped_like(term: str) -> str:
    """Treat search terms literally, including SQL LIKE wildcard characters."""
    value = term.strip().lower().replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return '%' + value + '%'


def paginate(conn: Connection, from_sql: str, select_sql: str, where: str, params: dict,
             order_sql: str, limit: int, offset: int) -> dict:
    """Internal use only; all SQL fragments are defined as literals in this module."""
    total = conn.execute(text(f"SELECT COUNT(*) {from_sql} {where}"), params).scalar_one()
    records = [dict(r) for r in conn.execute(
        text(f"SELECT {select_sql} {from_sql} {where} ORDER BY {order_sql} LIMIT :limit OFFSET :offset"),
        {**params, "limit": limit, "offset": offset},
    ).mappings()]
    return {"data": records, "pagination": {"total": total, "limit": limit, "offset": offset,
                                               "has_more": offset + len(records) < total},
            "notice": NOTICE}


def mappings_by_occupation(conn: Connection, occupation_ids: list[str]) -> dict[str, list[dict]]:
    result = {key: [] for key in occupation_ids}
    if not occupation_ids:
        return result
    query = text("""
        SELECT occupation_id, kbji_edition, kbji_code, kbji_label_id,
               source_id, verified_by, verified_at
        FROM kbji_mappings WHERE occupation_id IN :ids
        ORDER BY kbji_edition, kbji_code
    """).bindparams(bindparam("ids", expanding=True))
    for row in conn.execute(query, {"ids": occupation_ids}).mappings():
        record = dict(row)
        # Date is serialized explicitly, consistent for PostgreSQL and SQLite.
        record["verified_at"] = str(record["verified_at"])
        result[record.pop("occupation_id")].append(record)
    return result


def occupation_rows(conn: Connection, where: str = "", params: dict | None = None,
                    limit: int = 100, offset: int = 0) -> dict:
    from_sql = "FROM occupations o JOIN sectors s ON s.sector_id = o.sector_id"
    selection = "o.occupation_id, o.preferred_name_id, o.alternative_names, o.description_id, o.record_status, o.source_id, o.last_reviewed, s.sector_id, s.sector_name"
    result = paginate(conn, from_sql, selection, where, params or {},
                      "o.preferred_name_id ASC, o.occupation_id ASC", limit, offset)
    mappings = mappings_by_occupation(conn, [r["occupation_id"] for r in result["data"]])
    for item in result["data"]:
        item["aliases"] = [a.strip() for a in (item.pop("alternative_names") or "").split("|") if a.strip()]
        item["kbji_mappings"] = mappings[item["occupation_id"]]
        item["last_reviewed"] = str(item["last_reviewed"]) if item["last_reviewed"] else None
    return result


def build_app(url: str | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.engine = engine_for(url or database_url())
        try:
            yield
        finally:
            app.state.engine.dispose()

    app = FastAPI(title="Registri Pekerjaan Indonesia (RPI)", version=VERSION,
                  description=NOTICE, lifespan=lifespan,
                  contact={"name": "NOR-ID maintainers"})
    allowed = [s.strip() for s in (os.getenv("RPI_CORS_ORIGINS") or os.getenv("NOR_CORS_ORIGINS", "")).split(",") if s.strip()]
    if allowed:
        app.add_middleware(CORSMiddleware, allow_origins=allowed,
                           allow_credentials=False, allow_methods=["GET"], allow_headers=["*"])

    @app.get("/healthz", tags=["health"])
    def health(request: Request):
        try:
            with db(request).connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ok", "api_version": VERSION}
        except SQLAlchemyError:
            raise HTTPException(status_code=503, detail="Database unavailable")

    @app.get("/v1/meta", tags=["metadata"])
    def meta(request: Request):
        with db(request).connect() as conn:
            occupations = conn.execute(text("SELECT COUNT(*) FROM occupations")).scalar_one()
            verified = conn.execute(text("SELECT COUNT(*) FROM kbji_mappings")).scalar_one()
            sectors = conn.execute(text("SELECT COUNT(*) FROM sectors")).scalar_one()
            published = conn.execute(text("SELECT COUNT(*) FROM occupations WHERE record_status='published'")).scalar_one()
        return {"api_version": VERSION, "occupations": occupations, "sectors": sectors,
                "verified_kbji_mappings": verified, "published_occupations": published,
                "source_of_truth": "Git CSV", "notice": NOTICE}

    @app.get("/v1/sectors", tags=["reference"])
    def sectors(request: Request):
        with db(request).connect() as conn:
            rows = conn.execute(text("""
                SELECT s.sector_id, s.sector_name, s.sector_type, COUNT(o.occupation_id) AS occupations_count
                FROM sectors s LEFT JOIN occupations o ON o.sector_id=s.sector_id
                GROUP BY s.sector_id, s.sector_name, s.sector_type
                ORDER BY s.sector_id
            """)).mappings()
            data = [dict(r) for r in rows]
        return {"data": data, "notice": "Sektor editorial; bukan kode KBLI atau kelompok KBJI."}

    @app.get("/v1/occupations", tags=["occupations"])
    def occupations(request: Request, q: Annotated[str, Query(max_length=150)] = "",
                    sector_id: Annotated[str | None, Query(max_length=20)] = None,
                    status: Annotated[str | None, Query(pattern="^(draft|reviewed|published|archived)$")] = None,
                    limit: Annotated[int, Query(ge=1, le=100)] = 25,
                    offset: Annotated[int, Query(ge=0, le=1000000)] = 0):
        filters = []
        params = {}
        if q.strip():
            filters.append("(LOWER(o.preferred_name_id) LIKE :q ESCAPE '\\' OR LOWER(o.alternative_names) LIKE :q ESCAPE '\\')")
            params["q"] = escaped_like(q)
        if sector_id:
            filters.append("o.sector_id = :sector_id")
            params["sector_id"] = sector_id
        if status:
            filters.append("o.record_status = :status")
            params["status"] = status
        where = "WHERE " + " AND ".join(filters) if filters else ""
        with db(request).connect() as conn:
            return occupation_rows(conn, where, params, limit, offset)

    @app.get("/v1/occupations/{occupation_id}", tags=["occupations"])
    def occupation(request: Request, occupation_id: str):
        with db(request).connect() as conn:
            records = occupation_rows(conn, "WHERE o.occupation_id=:occupation_id",
                                      {"occupation_id": occupation_id}, 1, 0)["data"]
            if not records:
                raise HTTPException(status_code=404, detail="Occupation not found")
            titles = conn.execute(text("""
                SELECT t.title_id,t.title_name_id,t.seniority_level,t.context_code,t.notes
                FROM job_titles t WHERE t.occupation_id=:occupation_id ORDER BY t.title_id
            """), {"occupation_id": occupation_id}).mappings()
            record = records[0]
            record["job_titles"] = [dict(t) for t in titles]
            return {"data": record, "notice": NOTICE}

    @app.get("/v1/job-titles", tags=["reference"])
    def job_titles(request: Request,
                   occupation_id: Annotated[str | None, Query(max_length=25)] = None,
                   q: Annotated[str, Query(max_length=150)] = "",
                   limit: Annotated[int, Query(ge=1, le=100)] = 25,
                   offset: Annotated[int, Query(ge=0, le=1000000)] = 0):
        filters = []
        params = {}
        if occupation_id:
            filters.append("t.occupation_id=:occupation_id")
            params["occupation_id"] = occupation_id
        if q.strip():
            filters.append("LOWER(t.title_name_id) LIKE :q ESCAPE '\\'")
            params["q"] = escaped_like(q)
        where = "WHERE " + " AND ".join(filters) if filters else ""
        with db(request).connect() as conn:
            return paginate(conn, "FROM job_titles t", "t.title_id,t.title_name_id,t.occupation_id,t.seniority_level,t.context_code,t.notes",
                            where, params, "t.title_name_id ASC, t.title_id ASC", limit, offset)

    @app.get("/v1/employment-contexts", tags=["reference"])
    def employment_contexts(request: Request):
        with db(request).connect() as conn:
            return {"data": [dict(r) for r in conn.execute(text("""
                SELECT context_code,label_id,dimension FROM employment_contexts
                ORDER BY context_code
            """)).mappings()]}

    @app.get("/v1/kbji/codes", tags=["kbji"])
    def kbji_codes(request: Request,
                   edition: Annotated[str | None, Query(max_length=40)] = None,
                   limit: Annotated[int, Query(ge=1, le=100)] = 25,
                   offset: Annotated[int, Query(ge=0, le=1000000)] = 0):
        """Only source-verified mappings. No fabricated placeholder official codes."""
        where = "WHERE k.kbji_edition=:edition" if edition else ""
        params = {"edition": edition} if edition else {}
        grouped = """FROM kbji_mappings k """ + where + " GROUP BY k.kbji_edition,k.kbji_code,k.kbji_label_id,k.source_id"
        with db(request).connect() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM (SELECT 1 " + grouped + ") counts"), params).scalar_one()
            data = [dict(r) for r in conn.execute(text("""
                SELECT k.kbji_edition,k.kbji_code,k.kbji_label_id,k.source_id,
                       COUNT(DISTINCT k.occupation_id) AS occupation_count """ + grouped +
                " ORDER BY k.kbji_edition,k.kbji_code LIMIT :limit OFFSET :offset"),
                {**params, "limit": limit, "offset": offset}).mappings()]
        return {"data": data, "pagination": {"total": total, "limit": limit, "offset": offset,
                                                "has_more": offset + len(data) < total},
                "notice": "Hanya pemetaan KBJI yang diverifikasi dan memiliki bukti sumber."}

    @app.get("/v1/exports/occupations.json", tags=["exports"])
    def download_json(request: Request):
        with db(request).connect() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM occupations")).scalar_one()
            records = []
            for offset in range(0, total, 100):
                records.extend(occupation_rows(conn, limit=100, offset=offset)["data"])
        payload = {"api_version": VERSION, "notice": NOTICE, "data": records}
        return Response(json.dumps(payload, ensure_ascii=False, default=str, indent=2) + "\n",
                        media_type="application/json; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="nor-id-occupations.json"'})

    @app.get("/v1/exports/occupations.csv", tags=["exports"])
    def download_csv(request: Request):
        with db(request).connect() as conn:
            total = conn.execute(text("SELECT COUNT(*) FROM occupations")).scalar_one()
            records = []
            for offset in range(0, total, 100):
                records.extend(occupation_rows(conn, limit=100, offset=offset)["data"])
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)
        writer.writerow(["occupation_id", "name", "aliases", "sector_id", "sector_name",
                         "record_status", "source_id", "verified_kbji_codes"])
        for record in records:
            writer.writerow([record["occupation_id"], record["preferred_name_id"],
                             "|".join(record["aliases"]), record["sector_id"], record["sector_name"],
                             record["record_status"], record["source_id"],
                             "|".join(m["kbji_code"] for m in record["kbji_mappings"])])
        return Response("\ufeff" + buffer.getvalue(), media_type="text/csv; charset=utf-8",
                        headers={"Content-Disposition": 'attachment; filename="nor-id-occupations.csv"'})

    from .api_indonesia import pasang_rute
    pasang_rute(app, db, escaped_like, paginate, occupation_rows)
    return app


app = build_app()
