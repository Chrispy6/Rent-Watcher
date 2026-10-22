CREATE TABLE listings (
    id TEXT PRIMARY KEY,
    formatted_address TEXT NOT NULL,
    city TEXT,
    state TEXT,
    price NUMERIC(12, 2) CHECK (price >= 0),
    bedrooms INTEGER CHECK (bedrooms >= 0),
    bathrooms NUMERIC(4, 1) CHECK (bathrooms >= 0),
    square_footage INTEGER CHECK (square_footage > 0)
);