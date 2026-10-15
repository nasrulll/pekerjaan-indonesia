-- NOR-ID / Pekerjaan Indonesia - PostgreSQL schema v0.2
-- Official KBJI/KBLI codes are stored only when source verified.
BEGIN;
CREATE TABLE IF NOT EXISTS data_sources (
  source_id text PRIMARY KEY,
  title text NOT NULL,
  publisher text NOT NULL,
  edition text,
  uri text,
  kind text NOT NULL CHECK (kind IN ('official','internal','academic','other')),
  license_note text
);

CREATE TABLE IF NOT EXISTS sectors (
  sector_id text PRIMARY KEY,
  sector_name text NOT NULL UNIQUE,
  sector_type text NOT NULL DEFAULT 'editorial' CHECK(sector_type IN ('editorial','official_kbli')),
  official_kbli_code text -- nullable until source verified; KBLI is an activity classification
);

CREATE TABLE IF NOT EXISTS occupations (
  occupation_id text PRIMARY KEY CHECK (occupation_id ~ '^ID-OCC-[0-9]{6}$'),
  preferred_name_id text NOT NULL,
  alternative_names text NOT NULL DEFAULT '',
  sector_id text NOT NULL REFERENCES sectors(sector_id),
  description_id text,
  source_id text NOT NULL REFERENCES data_sources(source_id),
  record_status text NOT NULL DEFAULT 'draft' CHECK(record_status IN ('draft','reviewed','published','archived')),
  last_reviewed date,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(preferred_name_id,sector_id)
);

-- Allow upgrading a database initialized with the v0.1 schema.
ALTER TABLE occupations ADD COLUMN IF NOT EXISTS alternative_names text NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS occupation_aliases (
  alias_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  occupation_id text NOT NULL REFERENCES occupations(occupation_id) ON DELETE CASCADE,
  alternative_name_id text NOT NULL,
  UNIQUE (occupation_id,alternative_name_id)
);

CREATE TABLE IF NOT EXISTS kbji_mappings (
  occupation_id text NOT NULL REFERENCES occupations(occupation_id),
  kbji_edition text NOT NULL,
  kbji_code text NOT NULL CHECK (kbji_code ~ '^[0-9]{1,8}$'),
  kbji_label_id text NOT NULL,
  source_id text NOT NULL REFERENCES data_sources(source_id),
  verified_by text NOT NULL,
  verified_at date NOT NULL,
  PRIMARY KEY (occupation_id,kbji_edition,kbji_code)
);

CREATE TABLE IF NOT EXISTS employment_contexts (
  context_code text PRIMARY KEY,
  label_id text NOT NULL,
  dimension text NOT NULL CHECK(dimension IN ('employment_status','employer_sector','work_arrangement'))
);

-- A person may hold a title in multiple contexts. Context is not part of the occupational identity.
CREATE TABLE IF NOT EXISTS job_titles (
  title_id text PRIMARY KEY,
  title_name_id text NOT NULL,
  occupation_id text NOT NULL REFERENCES occupations(occupation_id),
  seniority_level text,
  context_code text REFERENCES employment_contexts(context_code),
  notes text
);

CREATE TABLE IF NOT EXISTS occupation_reviews (
  review_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  occupation_id text NOT NULL REFERENCES occupations(occupation_id),
  reviewer text NOT NULL,
  outcome text NOT NULL CHECK(outcome IN ('approved','rejected','needs_changes')),
  notes text,
  reviewed_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_occupation_name ON occupations(preferred_name_id);
CREATE INDEX IF NOT EXISTS ix_occupation_sector ON occupations(sector_id);
CREATE INDEX IF NOT EXISTS ix_occupation_status ON occupations(record_status);
CREATE INDEX IF NOT EXISTS ix_kbji_code ON kbji_mappings(kbji_edition,kbji_code);
CREATE INDEX IF NOT EXISTS ix_title_occupation ON job_titles(occupation_id);
COMMIT;
