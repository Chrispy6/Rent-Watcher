-- INITIAL SETUP: run once in a new database; this is not an incremental migration.
-- The request-attempt table is initialized separately (see README).
CREATE TABLE listings (
    -- Provider IDs are unique; imports use this key to decide whether to insert or update.
    id TEXT PRIMARY KEY,
    -- Every stored record needs an address; columns without NOT NULL may be unknown.
    formatted_address TEXT NOT NULL,
    city TEXT,
    state TEXT,
    -- NUMERIC stores exact decimal values; precision includes digits on both sides.
    -- CHECK constraints reject invalid present values; SQL NULL remains allowed here.
    price NUMERIC(12, 2) CHECK (price >= 0),
    bedrooms INTEGER CHECK (bedrooms >= 0),
    bathrooms NUMERIC(4, 1) CHECK (bathrooms >= 0),
    -- Importers convert nonpositive sizes to NULL to satisfy this constraint.
    square_footage INTEGER CHECK (square_footage > 0)
);