import json
import os
from pathlib import Path

import psycopg

from update_listings import validate_listings


project_folder = Path(__file__).resolve().parent.parent
pending_file = project_folder / "Golden_Listings.pending.json"

with pending_file.open("r", encoding="utf-8") as file:
    listings = json.load(file)

validate_listings(listings)

# Prepare the values before making database changes.
rows = []

for listing in listings:
    square_footage = listing.get("squareFootage")

    if square_footage is not None and square_footage <= 0:
        square_footage = None

    rows.append(
        (
            listing["id"],
            listing["formattedAddress"],
            listing["city"],
            listing["state"],
            listing.get("price"),
            listing.get("bedrooms"),
            listing.get("bathrooms"),
            square_footage,
        )
    )

listing_ids = [listing["id"] for listing in listings]

with psycopg.connect(
    os.environ["DATABASE_URL"],
    connect_timeout=15,
) as connection:
    with connection.cursor() as cursor:
        # Prevent overlapping imports from changing listings simultaneously.
        cursor.execute("LOCK TABLE listings IN EXCLUSIVE MODE")

        cursor.executemany(
            """
            INSERT INTO listings (
                id, formatted_address, city, state,
                price, bedrooms, bathrooms, square_footage
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                formatted_address = EXCLUDED.formatted_address,
                city = EXCLUDED.city,
                state = EXCLUDED.state,
                price = EXCLUDED.price,
                bedrooms = EXCLUDED.bedrooms,
                bathrooms = EXCLUDED.bathrooms,
                square_footage = EXCLUDED.square_footage;
            """,
            rows,
        )

        # Remove Golden listings absent from the complete active results.
        cursor.execute(
            """
            DELETE FROM listings
            WHERE city = %s
              AND state = %s
              AND NOT (id = ANY(%s::text[]));
            """,
            ("Golden", "CO", listing_ids),
        )

        removed = cursor.rowcount

# Success here means the connection block committed all changes.
print(f"Imported or updated {len(listings)} active listings.")
print(f"Removed {removed} previously stored Golden listings.")