"""Allowed SQL identifier column names for catalog ingestion."""
# Fixed column names prevent a modified CSV header from being interpreted as SQL.
COLUMNS = {
    "data_sources": ("source_id", "title", "publisher", "edition", "uri", "kind", "license_note"),
    "sectors": ("sector_id", "sector_name", "sector_type", "official_kbli_code"),
    "occupations": ("occupation_id", "preferred_name_id", "alternative_names", "sector_id",
                    "description_id", "source_id", "record_status", "last_reviewed"),
    "employment_contexts": ("context_code", "label_id", "dimension"),
    "job_titles": ("title_id", "title_name_id", "occupation_id", "seniority_level", "context_code", "notes"),
    "kbji_mappings": ("occupation_id", "kbji_edition", "kbji_code", "kbji_label_id",
                       "source_id", "verified_by", "verified_at"),
}

