-- Migrasi tambahan v0.4 untuk PostgreSQL yang sudah terpasang v0.3; idempoten.
BEGIN;
CREATE TABLE IF NOT EXISTS pemetaan_internasional (
 id_pemetaan text PRIMARY KEY, id_pekerjaan text NOT NULL REFERENCES occupations(occupation_id),
 sistem_klasifikasi text NOT NULL, edisi text NOT NULL, kode text NOT NULL,
 nama_resmi text NOT NULL, sumber_id text NOT NULL REFERENCES data_sources(source_id),
 diverifikasi_oleh text NOT NULL, tanggal_verifikasi date NOT NULL,
 UNIQUE(id_pekerjaan,sistem_klasifikasi,edisi,kode));
CREATE TABLE IF NOT EXISTS riwayat_rilis (versi text PRIMARY KEY, hash_manifest text NOT NULL,
 waktu_rilis timestamptz NOT NULL, status text NOT NULL);
COMMIT;
