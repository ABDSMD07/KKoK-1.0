-- ============================================================
-- PS 26018 - Land Record Intelligence System
-- PostgreSQL V1.0 Schema
-- ============================================================

-- ------------------------------------------------------------
-- 1. DOCUMENTS
-- One row represents one processed land-record document.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR(255) PRIMARY KEY,

    status VARCHAR(50) NOT NULL,

    created_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    human_verification_version VARCHAR(20),
    confidence_version VARCHAR(20),
    validation_version VARCHAR(20),
    normalization_version VARCHAR(20),
    extraction_version VARCHAR(20),

    duplicate_classification VARCHAR(50),
    duplicate_review_required BOOLEAN NOT NULL DEFAULT FALSE,

    total_fields INTEGER NOT NULL DEFAULT 0,
    fields_requiring_review INTEGER NOT NULL DEFAULT 0,
    fields_reviewed INTEGER NOT NULL DEFAULT 0,
    fields_accepted INTEGER NOT NULL DEFAULT 0,
    fields_auto_accepted INTEGER NOT NULL DEFAULT 0,
    fields_edited INTEGER NOT NULL DEFAULT 0,
    fields_rejected INTEGER NOT NULL DEFAULT 0,
    fields_pending INTEGER NOT NULL DEFAULT 0,

    created_in_database_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ------------------------------------------------------------
-- 2. LAND RECORD FIELDS
-- One row represents one field belonging to one document.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS land_record_fields (
    id BIGSERIAL PRIMARY KEY,

    document_id VARCHAR(255) NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    field_name VARCHAR(100) NOT NULL,

    machine_value TEXT,
    raw_value TEXT,
    normalized_value TEXT,
    verified_value TEXT,

    decision VARCHAR(50) NOT NULL,

    review_required BOOLEAN NOT NULL DEFAULT FALSE,

    validation_status VARCHAR(50),
    confidence_score NUMERIC(6,2),
    confidence_level VARCHAR(30),
    confidence_reason TEXT,

    human_reason TEXT,

    UNIQUE(document_id, field_name)
);


-- ------------------------------------------------------------
-- 3. EVIDENCE
-- Preserves where each field value came from.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence (
    id BIGSERIAL PRIMARY KEY,

    document_id VARCHAR(255) NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    field_name VARCHAR(100) NOT NULL,

    source_text TEXT,

    source_line_ids JSONB,
    source_page INTEGER,
    source_bbox JSONB,

    evidence_type VARCHAR(100),
    matched_label TEXT
);


-- ------------------------------------------------------------
-- 4. VERIFICATION AUDIT
-- Stores every human verification action.
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS verification_audit (
    id BIGSERIAL PRIMARY KEY,

    document_id VARCHAR(255) NOT NULL
        REFERENCES documents(document_id)
        ON DELETE CASCADE,

    field_name VARCHAR(100),

    event_type VARCHAR(100) NOT NULL,

    decision VARCHAR(50),

    reviewer VARCHAR(255),

    human_reason TEXT,

    event_timestamp TIMESTAMPTZ NOT NULL,

    event_details JSONB
);


-- ------------------------------------------------------------
-- INDEXES
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_land_record_fields_document_id
    ON land_record_fields(document_id);

CREATE INDEX IF NOT EXISTS idx_land_record_fields_field_name
    ON land_record_fields(field_name);

CREATE INDEX IF NOT EXISTS idx_evidence_document_id
    ON evidence(document_id);

CREATE INDEX IF NOT EXISTS idx_evidence_field_name
    ON evidence(field_name);

CREATE INDEX IF NOT EXISTS idx_verification_audit_document_id
    ON verification_audit(document_id);

CREATE INDEX IF NOT EXISTS idx_verification_audit_field_name
    ON verification_audit(field_name);


-- ============================================================
-- END OF PS 26018 POSTGRESQL V1.0 SCHEMA
-- ============================================================